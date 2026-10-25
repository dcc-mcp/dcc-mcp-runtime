# Verified staged Runtime launch contract

This first implementation slice verifies **already staged** local bundles and
generates a launch plan. It does not download CPython, install packages, activate
a version, start an adapter, or establish native application acceptance.
The existing `plan_install` and its host-owned installer boundary remain unchanged.

The operator's trust service must independently approve a bundle lock digest.
A digest supplied only by the downloaded bundle is not a trust anchor. Signature
verification, archive extraction, permissions, immutable staging and rollback
belong to that installer. No installer executor or complete CPython distribution
is supplied by this change or established by the v0.2.0 release assets.

## Bundle lock v1

Keep this JSON lock outside the staged root. Every regular file under the root
must occur exactly in `files` with its real lowercase SHA-256 digest. Links and
Windows reparse points are rejected. The inventory includes the interpreter,
standard library, Core/Runtime/adapter distributions, metadata and both manifests.
Empty directories may be omitted. Do not populate the digest placeholders below
with zeroes; compute them from the reviewed distribution and pin the lock digest
through the trust service.

```json
{
  "schema_version": "1",
  "python_executable": "python.exe",
  "site_packages": "lib/site-packages",
  "adapter_id": "figma",
  "adapter_distribution": "dcc-mcp-figma",
  "entry_module": "dcc_mcp_figma",
  "files": {
    "python.exe": "<actual interpreter digest>",
    "runtime/manifest.json": "<actual runtime manifest digest>",
    "runtime/manifests/figma.json": "<actual adapter manifest digest>"
  }
}
```

The example inventory is abbreviated and is not executable evidence or a shipped
Figma manifest. All payload files must be added. Runtime `python_version` is the
exact observed three-component version; ABI is `cp<major><minor>-` followed by
`sysconfig.get_platform()` with hyphens/dots replaced by underscores. The
interpreter's `sys.prefix` must resolve to the bundle root.

## Prepare and consume

`prepare_launch(root, lock_path, expected_lock_sha256, timeout=10)` verifies the
lock and full inventory before executing a bounded metadata probe using that
exact interpreter. Calling it explicitly authorizes that probe. The caller must
not invoke it merely because it discovered a directory or manifest.

```text
python -m dcc_mcp_runtime.cli prepare-launch <staged-root> <lock.json> --expected-lock-sha256 <operator-approved-lock-digest>
```

Both the probe and returned argv use `-I -S -B`: ignore user/environment Python
paths, skip automatic site and `.pth` execution, and suppress bytecode writes.
The reviewed bundle's site-packages is explicitly inserted. The probe reads
distribution metadata without importing adapter code. It checks actual Python
version/ABI, Runtime and adapter versions and actual Core version against **both**
unchanged PEP 440 requirements. `negotiate(..., core_version=...)` supports this
concrete version check; callers without it retain the old conservative comparison.

The returned `argv`, `cwd`, lock digest and probe report are data for the existing
host-owned launcher. No shell or PATH interpreter lookup is used. Errors, nonzero
exit, timeout, malformed output and mismatches produce no plan. Exceptions remain
visible to callers (the CLI exits nonzero).

The host must keep staging immutable during verification/execution, reverify on
reuse and obtain confirmation for the exact launch. A plan is not a reusable
authorization receipt. No global environment variables or active Runtime pointer
are changed. Isolation here is Python import-path isolation, not an OS sandbox;
native libraries and subprocess behavior still require host-owned policy.

## Remaining delivery gates

- Trusted CPython payload production, signatures and complete lock inventory.
- Real Figma manifest/wheel digest, entry-point and dependency closure from its owner.
- Host-owned installation/activation/rollback and write-protected staging.
- Actual staged-interpreter probe on each platform, then approved adapter launch.
- Figma Plugin API pairing and native read/write/save/reopen/export acceptance.

Repository inspection found only README clarification PR #4 open at the starting
main revision `3a54f666c4283bab160dbab3ac90630c9ed39087`; no active implementation
owner was confirmed from the available task inventory. This PR owns only this
shared verification/launch-plan slice and does not claim to resume another writer.
