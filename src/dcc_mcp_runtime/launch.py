"""Verify an operator-pinned staged bundle and probe it before planning a launch.

No downloader, installer, activation or adapter process launcher lives here.
The caller must obtain the lock digest from its trust service, not the bundle.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import subprocess
from pathlib import Path

from .handshake import negotiate
from .manifest import AdapterManifest, RuntimeManifest, load_manifest

# -I ignores environment/user paths; -S skips site/.pth execution; -B avoids writes.
_BOOTSTRAP = """
import sys
sys.path.insert(0, sys.argv.pop(1))
"""
_PROBE = (
    _BOOTSTRAP
    + """
import importlib.metadata as metadata, json, sysconfig
print(json.dumps({
    'prefix': sys.prefix,
    'base_prefix': sys.base_prefix,
    'search_paths': sys.path,
    'python_version': '.'.join(map(str, sys.version_info[:3])),
    'python_abi': 'cp%d%d-' % sys.version_info[:2] +
        sysconfig.get_platform().replace('-', '_').replace('.', '_'),
    'versions': {name: metadata.version(name) for name in sys.argv[1:]},
}))
"""
)
_LAUNCH = (
    _BOOTSTRAP
    + """
import runpy
runpy.run_module(sys.argv.pop(1), run_name='__main__', alter_sys=True)
"""
)


def _digest(path: Path) -> str:
    with path.open("rb") as stream:
        digest = hashlib.sha256()
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _inside(root: Path, relative: str) -> Path:
    path = root / relative
    if not relative or Path(relative).is_absolute() or ".." in Path(relative).parts:
        raise ValueError("bundle paths must be relative without traversal")
    if not path.resolve().is_relative_to(root):
        raise ValueError("bundle path escapes root")
    return path


def prepare_launch(
    root: str | Path,
    lock_path: str | Path,
    expected_lock_sha256: str,
    *,
    timeout: float = 10,
) -> dict:
    """Probe only a fully hashed local bundle; return argv for a host-owned launcher.

    Calling this explicitly authorizes execution of that bundle's interpreter for
    the bounded metadata probe. It does not authorize installing or launching it.
    """
    root, lock_path = Path(root).resolve(), Path(lock_path).resolve()
    if not math.isfinite(timeout) or not 0 < timeout <= 60:
        raise ValueError("probe timeout must be between 0 and 60 seconds")
    if not re.fullmatch(r"[0-9a-f]{64}", expected_lock_sha256):
        raise ValueError("a trusted lowercase SHA-256 lock digest is required")
    lock_bytes = lock_path.read_bytes()
    if hashlib.sha256(lock_bytes).hexdigest() != expected_lock_sha256:
        raise ValueError("lock digest mismatch")
    lock = json.loads(lock_bytes)
    if lock["schema_version"] != "1":
        raise ValueError("unsupported bundle lock schema")
    files = lock["files"]
    if not isinstance(files, dict) or not files:
        raise ValueError("nonempty complete file inventory required")
    expected = set()
    for relative, digest in files.items():
        path = _inside(root, relative)
        if not re.fullmatch(r"[0-9a-f]{64}", digest) or _digest(path) != digest:
            raise ValueError("bundle file digest mismatch: " + relative)
        expected.add(path)
    actual = set()
    for path in root.rglob("*"):
        if path.is_symlink() or getattr(path.lstat(), "st_file_attributes", 0) & 0x400:
            raise ValueError("bundle links are not allowed")
        if path.is_file():
            actual.add(path)
    if actual != expected:
        raise ValueError("bundle inventory mismatch")
    interpreter = _inside(root, lock["python_executable"])
    site = _inside(root, lock["site_packages"])
    if interpreter not in expected or not site.is_dir():
        raise ValueError("interpreter or isolated site-packages missing")
    adapter_id = lock["adapter_id"]
    module = lock["entry_module"]
    if not re.fullmatch(r"[A-Za-z0-9_-]+", adapter_id):
        raise ValueError("invalid adapter id")
    if not re.fullmatch(r"[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*", module):
        raise ValueError("invalid entry module")
    runtime = load_manifest(root / "runtime" / "manifest.json")
    adapter = load_manifest(root / "runtime" / "manifests" / (adapter_id + ".json"))
    if not isinstance(runtime, RuntimeManifest) or not isinstance(adapter, AdapterManifest):
        raise ValueError("invalid runtime/adapter manifest shapes")
    if adapter.adapter_id != adapter_id:
        raise ValueError("adapter identity mismatch")
    names = ["dcc-mcp-core", "dcc-mcp-runtime", lock["adapter_distribution"]]
    result = subprocess.run(
        [str(interpreter), "-I", "-S", "-B", "-c", _PROBE, str(site), *names],
        cwd=root,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=True,
    )
    report = json.loads(result.stdout)
    if Path(report["prefix"]).resolve() != root:
        raise ValueError("interpreter prefix is outside the bundle")
    if Path(report["base_prefix"]).resolve() != root or any(
        not Path(path).resolve().is_relative_to(root) for path in report["search_paths"]
    ):
        raise ValueError("interpreter depends on paths outside the bundle")
    if (
        report["python_version"] != runtime.python_version
        or report["python_abi"] != runtime.python_abi
    ):
        raise ValueError("probed Python version/ABI mismatch")
    versions = report["versions"]
    if versions["dcc-mcp-runtime"] != runtime.version or versions[names[2]] != adapter.version:
        raise ValueError("probed package version mismatch")
    handshake = negotiate(runtime, adapter, core_version=versions["dcc-mcp-core"])
    if not handshake.accepted:
        raise ValueError(handshake.reason)
    return {
        "argv": [str(interpreter), "-I", "-S", "-B", "-c", _LAUNCH, str(site), module],
        "cwd": str(root),
        "lock_sha256": expected_lock_sha256,
        "probe": report,
        "adapter_id": adapter_id,
        "requires_confirmation": True,
        "native_acceptance": "not_run",
    }
