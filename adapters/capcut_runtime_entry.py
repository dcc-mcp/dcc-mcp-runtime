"""Drop-in entry point for dcc-mcp-capcut in the shared runtime."""

from dcc_mcp_runtime.bootstrap import require_adapter


def main() -> None:
    require_adapter("capcut")
    from dcc_mcp_capcut.server import start_server

    start_server()


if __name__ == "__main__":
    main()
