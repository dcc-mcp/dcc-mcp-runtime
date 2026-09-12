"""Standalone Adobe/After Effects bridge entry point.

The selected standalone DCC-MCP adapter is ``dcc-mcp-aftereffects``. The
``adobepy`` repository remains an SDK/broker and is not launched here.
"""

from dcc_mcp_runtime.bootstrap import require_adapter


def main() -> None:
    require_adapter("adobe")
    from dcc_mcp_aftereffects.server import start_server

    start_server()


if __name__ == "__main__":
    main()
