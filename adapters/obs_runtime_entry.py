"""Drop-in entry point for dcc-mcp-obs in the shared runtime."""

from dcc_mcp_runtime.bootstrap import require_adapter


def main() -> None:
    require_adapter("obs")
    # The shared runtime owns Python and transport; OBS owns its native plugin
    # and WebSocket bridge. Avoid the legacy self-contained wrapper.
    from dcc_mcp_obs.server import main as obs_main

    obs_main()


if __name__ == "__main__":
    main()
