"""The source-matched adapter candidate is data, not an installed Runtime."""

from dcc_mcp_runtime.handshake import negotiate
from dcc_mcp_runtime.manifest import AdapterManifest, load_manifest


def test_figma_candidate_keeps_exact_wheel_and_compatibility_boundaries():
    """Keep the real wheel pin separate from the unverified cp311 payload target."""
    candidate = load_manifest("docs/examples/figma-adapter.cp311-win_amd64.json")
    assert isinstance(candidate, AdapterManifest)
    assert (candidate.adapter_id, candidate.version) == ("figma", "0.1.0")
    assert (
        candidate.wheel_sha256 == "611e5afca59f861b71ef6ff41d19ce315be05fa813311fdc40f3d3efc97c5a39"
    )
    assert candidate.signature is None
    assert candidate.host_mode == "external"
    assert candidate.python_abi == "cp311-win_amd64"
    assert candidate.dcc_mcp_core == ">=0.20.44,<0.21"
    assert set(candidate.capabilities) == {
        "document.read",
        "node.read",
        "frame.create",
        "frame.update",
        "node.export",
        "design.blueprint.apply",
        "design.blueprint.read",
    }
    declared = load_manifest("runtime/manifest.json")
    assert not negotiate(declared, candidate).accepted
    assert negotiate(declared, candidate, core_version="0.20.44").accepted
    assert not negotiate(declared, candidate, core_version="0.21.0").accepted
