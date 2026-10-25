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
  "entry_args": ["serve", "--bridge-port", "19061", "--mcp-port", "0", "--token-env", "DCC_MCP_FIGMA_TOKEN", "--request-timeout", "120"],
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

`entry_args` is an optional exact string array, covered by the trusted lock digest.
It defaults to no arguments for existing locks. Figma 0.1.0 requires `serve` to
start its explicit service; no token value belongs in this lock or argv. The
existing operator-provided token environment and Plugin API route are unchanged.
Preparing a plan does not invoke `serve`, create a token or grant pairing access.

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

`core_launch_plan` is the existing Core schema-v1 document, not a second launcher:
`schema_version`, `dcc_type`, absolute `executable`, exact `argv`, adapter `version`,
empty `project_markers` and `cwd`. The operator may separately publish this nested
document through Core's explicit `--launch-plan` route after reviewing the exact
operation. This API does not write project receipts or registry configuration,
invoke `start-instance`, bypass its `--yes` gate, or claim registration/readiness.
Reserved Core expansion tokens in pinned paths/arguments are rejected so Core
cannot silently reinterpret an approved path or argument. Contract source:
[Core launch plan v1](https://github.com/dcc-mcp/dcc-mcp-core/blob/47787b991b3441b62c6a037013668d306b9396e7/docs/guide/adapter-launch-plan-contract.md).

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

### Figma source/package evidence

The reviewed Figma source revision is
[`b7d1dc108bd0f334754aa00af8ebbd6b6e65af81`](https://github.com/dcc-mcp/dcc-mcp-figma/tree/b7d1dc108bd0f334754aa00af8ebbd6b6e65af81).
Its package declares 0.1.0 and `dcc-mcp-core>=0.20.44,<0.21`; the existing
`cp311-win_amd64` route remains a target, not an interpreter acceptance receipt.
One available local 61,707-byte wheel had SHA-256
`9a1337f6cbd3ff030ee115092b00e20b8734a38eea90fcc7c29bcbc1d388880a`.
Its `binding.py`, `blueprint.py`, `http_bridge.py` and `__main__.py` differed from
the canonical Git blobs at that revision (not just line endings). Therefore its
digest is **not** published as the current Figma adapter manifest or a trusted
payload. This finding applies to that local candidate, not every CI-built wheel.
No existing wheel was overwritten by this Runtime task, and no placeholder wheel
hash was installed.

The owner subsequently supplied a canonical 63,920-byte wheel with SHA-256
`611e5afca59f861b71ef6ff41d19ce315be05fa813311fdc40f3d3efc97c5a39`.
Runtime independently compared all 17 package Python/plugin files against the
raw Git blobs at that source revision and verified all 21 hashed RECORD entries.
The [adapter candidate](examples/figma-adapter.cp311-win_amd64.json) pins those
actual bytes, seven declared capabilities and the unchanged Core requirement.
It is kept under documentation, not in the shipped `runtime/manifests` directory:
the wheel is pure Python (`py3-none-any`, Requires-Python >=3.7), while cp311 Windows
is still an unobserved payload target. Its null signature does not establish
trusted authority. Neither the wheel nor candidate is a complete Runtime lock.
No wheel was imported, extracted into an environment or executed for this check.

Production dependency remains Core `>=0.20.44,<0.21`. The optional trial client
uses MCP `>=1.27,<2` on Python >=3.10; pytest and hatchling are not production
requirements. A complete, independently approved CPython/Core/Runtime/dependency
inventory and actual staged-interpreter probe are still required before placing
an ABI-bound Figma manifest in a managed Runtime. No Runtime version is inferred
from the old example manifest's 0.1.0 value.

Repository inspection found only README clarification PR #4 open at the starting
main revision `3a54f666c4283bab160dbab3ac90630c9ed39087`; no active implementation
owner was confirmed from the available task inventory. This PR owns only this
shared verification/launch-plan slice and does not claim to resume another writer.
