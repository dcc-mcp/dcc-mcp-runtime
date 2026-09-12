"""Runtime/adapter capability negotiation."""

from __future__ import annotations

from dataclasses import dataclass

from .manifest import AdapterManifest, RuntimeManifest


@dataclass(frozen=True)
class CapabilityHandshake:
    runtime_id: str
    runtime_version: str
    python_abi: str
    dcc_mcp_core: str
    adapter_id: str
    adapter_version: str
    capabilities: tuple[str, ...]
    capabilities_fingerprint: str


@dataclass(frozen=True)
class HandshakeResult:
    accepted: bool
    reason: str
    handshake: CapabilityHandshake | None = None


def negotiate(runtime: RuntimeManifest, adapter: AdapterManifest) -> HandshakeResult:
    if adapter.host_mode == "embedded":
        return HandshakeResult(False, "embedded_adapter_requires_host_runtime")
    if runtime.python_abi != adapter.python_abi:
        return HandshakeResult(False, "python_abi_mismatch")
    if runtime.dcc_mcp_core != adapter.dcc_mcp_core:
        return HandshakeResult(False, "dcc_mcp_core_mismatch")
    capabilities = tuple(sorted(set(adapter.capabilities)))
    # The runtime does not sign/authorise capabilities; it carries a stable
    # handshake value for the gateway to compare with its catalog.
    import hashlib

    fingerprint = hashlib.sha256("\n".join(capabilities).encode()).hexdigest()
    return HandshakeResult(
        True,
        "accepted",
        CapabilityHandshake(
            runtime.runtime_id,
            runtime.version,
            runtime.python_abi,
            runtime.dcc_mcp_core,
            adapter.adapter_id,
            adapter.version,
            capabilities,
            fingerprint,
        ),
    )
