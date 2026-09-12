from pathlib import Path

from dcc_mcp_runtime.bootstrap import negotiate_adapter, runtime_root


def test_runtime_root_can_be_explicit(monkeypatch):
    monkeypatch.setenv("DCC_MCP_RUNTIME_ROOT", str(Path.cwd()))
    assert runtime_root() == Path.cwd().resolve()


def test_capcut_and_obs_compatibility_entries_handshake(monkeypatch):
    monkeypatch.setenv("DCC_MCP_RUNTIME_ROOT", str(Path.cwd()))
    assert negotiate_adapter("capcut").accepted
    assert negotiate_adapter("obs").accepted
