"""Strict, serialisable runtime and adapter manifests.

The manifest is deliberately data-only so it can be verified before importing
any adapter code. Hash/signature fields are opaque strings; signature checking
is delegated to the operator-owned trust service.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "1"


@dataclass(frozen=True)
class AdapterManifest:
    adapter_id: str
    version: str
    dcc_mcp_core: str
    python_abi: str
    capabilities: tuple[str, ...]
    wheel_sha256: str
    signature: str | None = None
    host_mode: str = "external"

    def __post_init__(self) -> None:
        if not self.adapter_id or not self.version or not self.python_abi:
            raise ValueError("adapter_id, version and python_abi are required")
        if self.host_mode not in {"external", "embedded"}:
            raise ValueError("host_mode must be external or embedded")
        if len(self.wheel_sha256) != 64:
            raise ValueError("wheel_sha256 must be a 64-character SHA-256 hex digest")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AdapterManifest:
        return cls(
            adapter_id=str(data["adapter_id"]),
            version=str(data["version"]),
            dcc_mcp_core=str(data["dcc_mcp_core"]),
            python_abi=str(data["python_abi"]),
            capabilities=tuple(str(x) for x in data.get("capabilities", [])),
            wheel_sha256=str(data["wheel_sha256"]),
            signature=data.get("signature"),
            host_mode=str(data.get("host_mode", "external")),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "adapter_id": self.adapter_id,
            "version": self.version,
            "dcc_mcp_core": self.dcc_mcp_core,
            "python_abi": self.python_abi,
            "capabilities": list(self.capabilities),
            "wheel_sha256": self.wheel_sha256,
            "signature": self.signature,
            "host_mode": self.host_mode,
        }


@dataclass(frozen=True)
class RuntimeManifest:
    runtime_id: str
    version: str
    python_version: str
    python_abi: str
    platform: str
    dcc_mcp_core: str
    adapters: tuple[AdapterManifest, ...] = field(default_factory=tuple)
    runtime_sha256: str | None = None
    signature: str | None = None
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError(f"unsupported manifest schema: {self.schema_version}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "runtime_id": self.runtime_id,
            "version": self.version,
            "python_version": self.python_version,
            "python_abi": self.python_abi,
            "platform": self.platform,
            "dcc_mcp_core": self.dcc_mcp_core,
            "runtime_sha256": self.runtime_sha256,
            "signature": self.signature,
            "adapters": [a.to_dict() for a in self.adapters],
        }


def load_manifest(path: str | Path) -> RuntimeManifest | AdapterManifest:
    """Load and validate either manifest shape without importing adapters."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if "runtime_id" in data:
        return RuntimeManifest(
            runtime_id=str(data["runtime_id"]),
            version=str(data["version"]),
            python_version=str(data["python_version"]),
            python_abi=str(data["python_abi"]),
            platform=str(data["platform"]),
            dcc_mcp_core=str(data["dcc_mcp_core"]),
            adapters=tuple(AdapterManifest.from_dict(x) for x in data.get("adapters", [])),
            runtime_sha256=data.get("runtime_sha256"),
            signature=data.get("signature"),
            schema_version=str(data.get("schema_version", SCHEMA_VERSION)),
        )
    return AdapterManifest.from_dict(data)
