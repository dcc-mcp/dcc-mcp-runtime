"""Consent-gated, verifiable and rollback-safe install planning."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class InstallPlan:
    operation_id: str
    runtime_id: str
    target_version: str
    package_path: str
    expected_sha256: str
    previous_version: str | None
    requires_confirmation: bool = True
    rollback_version: str | None = None


@dataclass(frozen=True)
class InstallResult:
    operation_id: str
    status: str
    active_version: str | None
    reason: str


def plan_install(
    *,
    operation_id: str,
    runtime_id: str,
    target_version: str,
    package_path: str,
    expected_sha256: str,
    previous_version: str | None = None,
) -> InstallPlan:
    """Return an exact plan; execution belongs to a host-owned allow-list."""
    if not operation_id or not runtime_id or not target_version or not package_path:
        raise ValueError("operation_id, runtime_id, target_version and package_path are required")
    if len(expected_sha256) != 64:
        raise ValueError("expected_sha256 must be a 64-character SHA-256 hex digest")
    return InstallPlan(
        operation_id,
        runtime_id,
        target_version,
        package_path,
        expected_sha256,
        previous_version,
        True,
        previous_version,
    )
