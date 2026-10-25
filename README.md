# dcc-mcp-runtime

Shared runtime contract and bootstrap tooling for **external** DCC-MCP adapters
(Adobe, CapCut and OBS). The published Python package provides manifest validation,
runtime/adapter compatibility negotiation, and typed installation/upgrade plans.

The side-by-side runtime design places CPython, `dcc-mcp-core` and adapter wheels
under `lib/site-packages`. This design is separate from verified distribution
availability. The [v0.2.0 GitHub Release](https://github.com/dcc-mcp/dcc-mcp-runtime/releases/tag/v0.2.0)
contains a Python wheel, source archive, runtime/adapter manifests and migration
guides; its listed assets do not include a complete bundled CPython runtime archive.
The checked-in `runtime/manifest.json` has no runtime digest or signature and lists
no bundled adapters, so it does not establish a usable bundled runtime.

Development uses `uv`/wheels. PyOxidizer packaging configuration is present, but
complete runtime artifacts and target-native acceptance must be verified before
claiming an installable bundled runtime.

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
