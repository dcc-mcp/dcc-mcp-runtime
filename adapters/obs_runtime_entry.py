"""Drop-in entry point for dcc-mcp-obs in the shared runtime."""

from dcc_mcp_runtime.bootstrap import require_adapter


def main() -> None:
    require_adapter("obs")
    from dcc_mcp_obs._standalone_entry import main as obs_main

    obs_main()


if __name__ == "__main__":
    main()
