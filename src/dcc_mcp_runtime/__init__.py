"""Shared runtime contracts for external DCC-MCP adapters."""

from .handshake import CapabilityHandshake, HandshakeResult, negotiate
from .lifecycle import InstallPlan, InstallResult, plan_install
from .manifest import AdapterManifest, RuntimeManifest, load_manifest

__all__ = [
    "AdapterManifest",
    "CapabilityHandshake",
    "HandshakeResult",
    "InstallPlan",
    "InstallResult",
    "RuntimeManifest",
    "load_manifest",
    "negotiate",
    "plan_install",
]
