"""Compatibility bootstrap used by external adapter entry points.

It performs only manifest loading and negotiation. Process spawning, host UI
control and installer execution remain owned by each adapter/core.
"""

from __future__ import annotations

import os
from pathlib import Path

from .handshake import HandshakeResult, negotiate
from .manifest import AdapterManifest, RuntimeManifest, load_manifest


def runtime_root() -> Path:
    """Resolve the side-by-side runtime root without consulting the shell."""
    configured = os.environ.get("DCC_MCP_RUNTIME_ROOT")
    if configured:
        return Path(configured).resolve()
    # Installed package: <root>/lib/site-packages/dcc_mcp_runtime.
    return Path(__file__).resolve().parents[3]


def negotiate_adapter(adapter_id: str) -> HandshakeResult:
    root = runtime_root()
    runtime = load_manifest(root / "runtime" / "manifest.json")
    adapter = load_manifest(root / "runtime" / "manifests" / f"{adapter_id}.json")
    if not isinstance(runtime, RuntimeManifest) or not isinstance(adapter, AdapterManifest):
        raise ValueError("runtime or adapter manifest has an invalid shape")
    return negotiate(runtime, adapter)


def require_adapter(adapter_id: str) -> HandshakeResult:
    result = negotiate_adapter(adapter_id)
    if not result.accepted:
        raise RuntimeError(f"DCC_MCP_RUNTIME_HANDSHAKE_FAILED:{result.reason}")
    return result
