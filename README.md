# dcc-mcp-runtime

Shared Python runtime for **external** DCC-MCP adapters (Adobe, CapCut and OBS).
The runtime is a versioned, side-by-side install containing CPython, `dcc-mcp-core`
and adapter wheels under `lib/site-packages`. Development still uses `uv`/wheels;
PyOxidizer is the reproducible distribution path.

Embedded DCC Python (Maya, Blender, Houdini, 3ds Max, etc.) is intentionally not
injected into this runtime. Those adapters keep their host interpreter and only
consume the same protocol/manifest contract.

## Quick start

```powershell
uv sync --extra dev
uv run pytest
uv run ruff check .
python -m build
```

`runtime/manifest.json` is the machine-readable contract. Validate an adapter
before loading it:

```powershell
python -m dcc_mcp_runtime.cli validate-manifest runtime/manifests/capcut.json
```

Installation and upgrade are represented by a typed plan. The runtime never
executes arbitrary shell/Python: an operator must approve an exact plan and a
host-owned installer performs the allow-listed operation. A failed health/hash
verification leaves the previous runtime active for rollback.

Releases use [release-please](https://github.com/googleapis/release-please):
Conventional Commits on `main` create a release PR; merging it creates the tag
and release, then the same workflow builds and uploads the wheel, sdist, and
runtime/adapter manifests to that exact release tag.

See [migration guides](docs/migration/) and [ADR 0001](docs/ADR-0001-shared-runtime.md).
