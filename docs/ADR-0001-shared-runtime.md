# ADR 0001: Shared runtime for external DCC adapters

## Decision

Adobe, CapCut and OBS use a side-by-side PyOxidizer runtime containing a
supported CPython build, `dcc-mcp-core`, and independently versioned adapter
wheels in `lib/site-packages`. Adapter startup performs a manifest/ABI/
capability handshake before registering with the gateway.

Maya, Blender, Houdini, 3ds Max and other embedded hosts retain their native
Python. They may consume the manifest protocol, but are never forced to load a
foreign interpreter or ABI.

## Integrity and lifecycle

Every runtime and wheel records SHA-256 and an operator-issued signature. The
installer receives an exact typed plan, requires explicit confirmation, verifies
the downloaded artifact before activation, and keeps the previous side-by-side
version until health and capability checks pass. Failed activation restores the
previous version. The runtime has no generic shell, registry, or raw Python
execution API.

PyOxidizer is a publishing mechanism; `uv sync`, wheel builds and normal Python
tests remain the development path.
