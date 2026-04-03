import sys

from mcp_client.app import McpClientApp


def main() -> None:
    app = McpClientApp()
    sys.exit(app.run())


if __name__ == "__main__":
    main()
