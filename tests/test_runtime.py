from dcc_mcp_runtime.handshake import negotiate
from dcc_mcp_runtime.lifecycle import plan_install
from dcc_mcp_runtime.manifest import AdapterManifest, RuntimeManifest, load_manifest

HASH = "a" * 64


def runtime() -> RuntimeManifest:
    return RuntimeManifest(
        runtime_id="test-runtime",
        version="1.0.0",
        python_version="3.11",
        python_abi="cp311-win_amd64",
        platform="windows-x86_64",
        dcc_mcp_core=">=0.19.13,<1.0.0",
    )


def adapter(**overrides) -> AdapterManifest:
    values = dict(
        adapter_id="capcut",
        version="0.1.0",
        dcc_mcp_core=">=0.19.13,<1.0.0",
        python_abi="cp311-win_amd64",
        capabilities=("timeline", "media"),
        wheel_sha256=HASH,
    )
    values.update(overrides)
    return AdapterManifest(**values)


def test_external_handshake_includes_stable_fingerprint():
    result = negotiate(runtime(), adapter())
    assert result.accepted is True
    assert result.handshake is not None
    assert len(result.handshake.capabilities_fingerprint) == 64


def test_embedded_adapter_is_not_injected():
    result = negotiate(runtime(), adapter(host_mode="embedded"))
    assert result == result.__class__(False, "embedded_adapter_requires_host_runtime")


def test_install_plan_requires_confirmation_and_rollback():
    plan = plan_install(
        operation_id="op-1",
        runtime_id="dcc-mcp-external",
        target_version="0.2.0",
        package_path="runtime-0.2.0.zip",
        expected_sha256=HASH,
        previous_version="0.1.0",
    )
    assert plan.requires_confirmation
    assert plan.rollback_version == "0.1.0"


def test_runtime_manifest_is_loadable():
    manifest = load_manifest("runtime/manifest.json")
    assert manifest.runtime_id == "dcc-mcp-external"
