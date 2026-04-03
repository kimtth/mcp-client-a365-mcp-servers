from __future__ import annotations

import json
import logging
import time
from pathlib import Path

log = logging.getLogger(__name__)

_CACHE_DIR = Path.home() / ".mcp-client-a365"
_TOOLS_CACHE_FILE = _CACHE_DIR / "tools-cache.json"
_MAX_CACHE_AGE_S = 24 * 60 * 60  # 24 hours


class CachedTool:
    __slots__ = ("name", "description", "input_schema", "server_name")

    def __init__(
        self, name: str, description: str, input_schema: dict, server_name: str
    ) -> None:
        self.name = name
        self.description = description
        self.input_schema = input_schema
        self.server_name = server_name

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.input_schema,
            "serverName": self.server_name,
        }

    @classmethod
    def from_dict(cls, data: dict) -> CachedTool:
        return cls(
            name=data["name"],
            description=data.get("description", ""),
            input_schema=data.get("inputSchema", {}),
            server_name=data.get("serverName", ""),
        )


def save_tools_cache(tools: list[CachedTool]) -> None:
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "timestamp": time.time(),
        "tools": [t.to_dict() for t in tools],
    }
    _TOOLS_CACHE_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    log.info("Cached %d tools to %s", len(tools), _TOOLS_CACHE_FILE)


def load_tools_cache() -> list[CachedTool] | None:
    try:
        if not _TOOLS_CACHE_FILE.exists():
            return None
        raw = json.loads(_TOOLS_CACHE_FILE.read_text(encoding="utf-8"))
        age = time.time() - raw["timestamp"]
        if age > _MAX_CACHE_AGE_S:
            log.info("Tool cache stale (%dh old), ignoring", int(age / 3600))
            return None
        tools = [CachedTool.from_dict(t) for t in raw["tools"]]
        log.info("Loaded %d cached tools (%dm old)", len(tools), int(age / 60))
        return tools
    except Exception as exc:
        log.warning("Failed to load tool cache: %s", exc)
        return None


def clear_tools_cache() -> None:
    try:
        if _TOOLS_CACHE_FILE.exists():
            _TOOLS_CACHE_FILE.unlink()
    except Exception:
        pass
