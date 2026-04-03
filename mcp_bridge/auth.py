from __future__ import annotations

import asyncio
import json
import logging
import time
from pathlib import Path
from typing import Any

import jwt
from azure.identity import (
    AuthenticationRecord,
    AzureCliCredential,
    ClientSecretCredential,
    DeviceCodeCredential,
    TokenCachePersistenceOptions,
)
from azure.core.credentials import TokenCredential

from mcp_bridge.config import AppConfig

log = logging.getLogger(__name__)

_REFRESH_BUFFER_SECONDS = 300  # 5 minutes

# A365 CLI stores tokens here after `a365 login`
_A365_CLI_TOKEN_PATH = (
    Path.home()
    / "AppData"
    / "Local"
    / "Microsoft.Agents.A365.DevTools.Cli"
    / "auth-token.json"
)

# Persistent auth record so Device Code is interactive only the first time
_AUTH_RECORD_DIR = (
    Path.home()
    / "AppData"
    / "Local"
    / "mcp-client-a365"
)
_AUTH_RECORD_PATH = _AUTH_RECORD_DIR / "auth-record.json"


def _load_auth_record() -> AuthenticationRecord | None:
    if not _AUTH_RECORD_PATH.exists():
        return None
    try:
        return AuthenticationRecord.deserialize(_AUTH_RECORD_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        log.debug("Could not load auth record: %s", exc)
        return None


def _save_auth_record(record: AuthenticationRecord) -> None:
    _AUTH_RECORD_DIR.mkdir(parents=True, exist_ok=True)
    _AUTH_RECORD_PATH.write_text(record.serialize(), encoding="utf-8")
    log.info("Auth record saved to %s", _AUTH_RECORD_PATH)


class TokenCache:
    """JWT-aware in-memory token cache with concurrent-request coalescing."""

    def __init__(self) -> None:
        self._token: str | None = None
        self._expires_at: float = 0
        self._pending: asyncio.Task[str] | None = None

    async def get_token(self, refresh_fn: callable) -> str:
        now = time.time()
        if self._token and now < self._expires_at - _REFRESH_BUFFER_SECONDS:
            return self._token

        if self._pending is not None:
            return await self._pending

        self._pending = asyncio.ensure_future(self._refresh(refresh_fn))
        try:
            return await self._pending
        finally:
            self._pending = None

    async def _refresh(self, refresh_fn: callable) -> str:
        token = await refresh_fn()
        self._token = token
        self._expires_at = self._extract_expiry(token)
        return token

    @staticmethod
    def _extract_expiry(token: str) -> float:
        try:
            decoded = jwt.decode(token, options={"verify_signature": False})
            if "exp" in decoded:
                return float(decoded["exp"])
        except Exception:
            pass
        return time.time() + 3600


def _load_a365_cli_token(resource_id: str) -> str | None:
    """Load a cached token from the A365 CLI auth-token.json file."""
    if not _A365_CLI_TOKEN_PATH.exists():
        return None
    try:
        data = json.loads(_A365_CLI_TOKEN_PATH.read_text(encoding="utf-8"))
        token = data.get("Tokens", {}).get(resource_id, {}).get("AccessToken")
        if not token:
            return None
        # Check expiry
        decoded = jwt.decode(token, options={"verify_signature": False})
        if decoded.get("exp", 0) < time.time() + _REFRESH_BUFFER_SECONDS:
            log.warning("A365 CLI token is expired or about to expire")
            return None
        return token
    except Exception as exc:
        log.debug("Could not load A365 CLI token: %s", exc)
        return None


def _decode_claims(token: str) -> dict[str, Any]:
    return jwt.decode(token, options={"verify_signature": False})


class TokenProvider:
    """Acquires tokens for Agent 365 MCP servers.

    Auth priority:
      1. Static bearer token (BEARER_TOKEN)
      2. A365 CLI cached token (from `a365 login`)
      3. Device Code (interactive, uses blueprint clientId — gets all consented scopes)
      4. Client credentials (clientId + clientSecret + tenantId)
      5. Azure CLI credential (az login)
    """

    def __init__(self, config: AppConfig) -> None:
        self._config = config
        self._cache = TokenCache()
        self._credential: TokenCredential | None = None
        self._device_code_credential: DeviceCodeCredential | None = None
        self._scopes = [config.mcp_platform_auth_scope]
        self._auth_mode = (config.mcp_auth_mode or "auto").strip().lower()
        # Extract resource ID from scope (e.g. "ea9ffc3e-.../.default" -> "ea9ffc3e-...")
        self._resource_id = config.mcp_platform_auth_scope.split("/")[0]
        self._device_code_callback: Any = None  # set externally by UI

        valid_modes = {"auto", "bearer", "a365-cli", "device-code", "client-secret", "azure-cli"}
        if self._auth_mode not in valid_modes:
            raise RuntimeError(
                f"Invalid MCP_AUTH_MODE. Expected one of: {', '.join(sorted(valid_modes))}"
            )

        self._init_credentials(config)

    def _init_credentials(self, config: AppConfig) -> None:
        # Device Code credential (uses the MCP Desktop Client app — gets all consented scopes)
        if config.mcp_client_id and config.mcp_tenant_id:
            cached_record = _load_auth_record()
            if cached_record:
                log.info("Device Code credential ready (cached auth record — silent mode)")
            else:
                log.info("Device Code credential ready (will prompt on first use)")

            def _prompt_callback(verification_uri: str, user_code: str, expires_on: Any) -> None:
                import webbrowser
                msg = (
                    f"\n{'='*50}\n"
                    f"SIGN IN REQUIRED\n"
                    f"Go to: {verification_uri}\n"
                    f"Enter code: {user_code}\n"
                    f"{'='*50}\n"
                )
                log.warning(msg)
                # Open browser automatically for the user
                webbrowser.open(verification_uri)
                if self._device_code_callback:
                    self._device_code_callback(verification_uri, user_code)

            self._device_code_credential = DeviceCodeCredential(
                tenant_id=config.mcp_tenant_id,
                client_id=config.mcp_client_id,
                cache_persistence_options=TokenCachePersistenceOptions(name="mcp-client-a365"),
                authentication_record=cached_record,
                prompt_callback=_prompt_callback,
            )

        # Client-secret credential (for daemon / app-only flows)
        if config.mcp_client_id and config.mcp_client_secret and config.mcp_tenant_id:
            log.info("Client-secret credential also configured for MCP")
            self._credential = ClientSecretCredential(
                tenant_id=config.mcp_tenant_id,
                client_id=config.mcp_client_id,
                client_secret=config.mcp_client_secret,
            )
        else:
            log.info("Azure CLI credential configured for MCP fallback")
            self._credential = AzureCliCredential()

    def is_configured(self) -> bool:
        return (
            bool(self._config.mcp_bearer_token)
            or _load_a365_cli_token(self._resource_id) is not None
            or self._device_code_credential is not None
            or self._credential is not None
        )

    def is_mock_mode(self) -> bool:
        return "localhost" in self._config.mcp_platform_endpoint

    async def get_token(self) -> str | None:
        if self.is_mock_mode():
            return None

        if self._auth_mode in {"auto", "bearer"} and self._config.mcp_bearer_token:
            log.info("Using static bearer token for MCP")
            return self._config.mcp_bearer_token

        # Try A365 CLI cached token (delegated, from `a365 login`)
        if self._auth_mode in {"auto", "a365-cli"}:
            cli_token = _load_a365_cli_token(self._resource_id)
            if cli_token:
                log.info("Using A365 CLI cached token for MCP")
                return cli_token

        # Device Code flow — authenticates as the blueprint app (gets all consented scopes)
        if self._auth_mode in {"auto", "device-code"} and self._device_code_credential:
            return await self._cache.get_token(self._acquire_device_code_token)

        if self._auth_mode == "device-code":
            raise RuntimeError(
                "MCP_AUTH_MODE=device-code requires MCP_CLIENT_ID and MCP_TENANT_ID"
            )

        if self._auth_mode == "client-secret" and not self._credential:
            raise RuntimeError("MCP_AUTH_MODE=client-secret requires client credentials")

        if self._auth_mode == "a365-cli":
            raise RuntimeError(
                "MCP_AUTH_MODE=a365-cli was requested, but no cached A365 CLI token is available"
            )

        if not self._credential:
            raise RuntimeError(
                "No authentication configured. "
                "Set BEARER_TOKEN, run 'a365 login', or configure MCP_CLIENT_ID."
            )

        if self._auth_mode == "azure-cli":
            log.info("Using Azure CLI credential for MCP")
        elif self._auth_mode == "client-secret":
            log.info("Using client-secret credential for MCP")
        else:
            log.info("Using configured credential fallback for MCP")

        return await self._cache.get_token(self._acquire_token)

    async def _acquire_device_code_token(self) -> str:
        loop = asyncio.get_running_loop()
        cred = self._device_code_credential

        try:
            if _load_auth_record():
                # We have a cached AuthenticationRecord — get_token() will be silent
                log.info("Attempting silent token acquisition with cached auth record")
                result = await loop.run_in_executor(None, cred.get_token, *self._scopes)
            else:
                # First time: authenticate() does interactive device code and
                # returns an AuthenticationRecord we persist for future silent auth
                log.info("Starting interactive device code authentication")
                record = await loop.run_in_executor(None, lambda: cred.authenticate(scopes=self._scopes))
                if record:
                    _save_auth_record(record)
                result = await loop.run_in_executor(None, cred.get_token, *self._scopes)
        except Exception as exc:
            log.error("Device code auth failed: %s", exc, exc_info=True)
            raise

        if not result or not result.token:
            raise RuntimeError("Device Code authentication failed")

        return result.token

    async def _acquire_token(self) -> str:
        result = self._credential.get_token(*self._scopes)
        if not result or not result.token:
            raise RuntimeError("Failed to acquire token")
        return result.token

    async def get_token_scopes(self) -> set[str]:
        token = await self.get_token()
        if not token:
            return set()
        try:
            claims = _decode_claims(token)
            return set((claims.get("scp") or "").split())
        except Exception:
            return set()
