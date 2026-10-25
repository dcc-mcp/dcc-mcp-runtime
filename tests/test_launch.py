"""Offline bundle fixtures never install or execute a Runtime interpreter."""

import hashlib
import json
import subprocess
import sys
from dataclasses import replace
from unittest.mock import patch

import pytest

from dcc_mcp_runtime.cli import main
from dcc_mcp_runtime.handshake import negotiate
from dcc_mcp_runtime.launch import _LAUNCH, _PROBE, prepare_launch
from test_runtime import adapter, runtime


def bundle(tmp_path):
    """Stage inert payload bytes and an independently pinned inventory."""
    root = tmp_path / "bundle"
    site = root / "lib" / "site-packages"
    site.mkdir(parents=True)
    (root / "python").write_bytes(b"inert test executable")
    manifests = root / "runtime" / "manifests"
    manifests.mkdir(parents=True)
    (root / "runtime" / "manifest.json").write_text(json.dumps(runtime().to_dict()))
    (manifests / "figma.json").write_text(
        json.dumps(adapter(adapter_id="figma", dcc_mcp_core=">=0.20.44,<0.21").to_dict())
    )
    (site / "package.py").write_text("# inert payload")
    lock = {
        "schema_version": "1",
        "python_executable": "python",
        "site_packages": "lib/site-packages",
        "adapter_id": "figma",
        "adapter_distribution": "dcc-mcp-figma",
        "entry_module": "dcc_mcp_figma",
        "files": {
            p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob("*")
            if p.is_file()
        },
    }
    lock_path = tmp_path / "lock.json"
    lock_path.write_text(json.dumps(lock))
    digest = hashlib.sha256(lock_path.read_bytes()).hexdigest()
    report = {
        "prefix": str(root),
        "base_prefix": str(root),
        "search_paths": [str(site), str(root / "lib")],
        "python_version": "3.11",
        "python_abi": "cp311-win_amd64",
        "versions": {
            "dcc-mcp-core": "0.20.44",
            "dcc-mcp-runtime": "1.0.0",
            "dcc-mcp-figma": "0.1.0",
        },
    }
    return root, lock_path, digest, report


def test_launch_plan_uses_pinned_interpreter_and_bounded_isolated_probe(tmp_path):
    """A mocked metadata probe yields a plan, never a business-process launch."""
    root, lock, digest, report = bundle(tmp_path)
    with patch("dcc_mcp_runtime.launch.subprocess.run") as run:
        run.return_value.stdout = json.dumps(report)
        plan = prepare_launch(root, lock, digest)
    assert run.call_count == 1
    assert run.call_args.args[0][:4] == [str(root / "python"), "-I", "-S", "-B"]
    assert run.call_args.kwargs["timeout"] == 10
    assert run.call_args.kwargs["check"] is True
    assert plan["requires_confirmation"]
    assert plan["native_acceptance"] == "not_run"
    assert plan["argv"][-1] == "dcc_mcp_figma"
    core = plan["core_launch_plan"]
    assert core["schema_version"] == 1
    assert core["dcc_type"] == "figma"
    assert core["executable"] == core["argv"][0] == str(root / "python")
    assert core["argv"] == plan["argv"]
    assert core["project_markers"] == []


@pytest.mark.parametrize("fault", ["digest", "tamper", "extra", "traversal", "missing"])
def test_untrusted_or_incomplete_payload_never_executes(tmp_path, fault):
    """Trust, complete inventory and containment checks precede execution."""
    root, lock, digest, _ = bundle(tmp_path)
    if fault == "digest":
        digest = "0" * 64
    elif fault == "tamper":
        (root / "python").write_text("tampered")
    elif fault == "extra":
        (root / "injected.pth").write_text("import dangerous")
    elif fault == "missing":
        (root / "python").unlink()
    else:
        data = json.loads(lock.read_text())
        data["files"]["../outside"] = "a" * 64
        lock.write_text(json.dumps(data))
        digest = hashlib.sha256(lock.read_bytes()).hexdigest()
    with patch("dcc_mcp_runtime.launch.subprocess.run") as run:
        with pytest.raises((ValueError, FileNotFoundError)):
            prepare_launch(root, lock, digest)
        run.assert_not_called()


@pytest.mark.parametrize(
    "fault", ["prefix", "paths", "abi", "version", "core", "timeout", "exit", "json"]
)
def test_probe_failure_never_produces_launch_plan(tmp_path, fault):
    """Actual interpreter/package facts must satisfy both original Core constraints."""
    root, lock, digest, report = bundle(tmp_path)
    if fault == "prefix":
        report["prefix"] = str(tmp_path)
    elif fault == "paths":
        report["search_paths"].append(str(tmp_path / "outside"))
    elif fault == "abi":
        report["python_abi"] = "cp312-win_amd64"
    elif fault == "version":
        report["versions"]["dcc-mcp-figma"] = "9.0"
    elif fault == "core":
        report["versions"]["dcc-mcp-core"] = "0.19.13"
    with patch("dcc_mcp_runtime.launch.subprocess.run") as run:
        run.return_value.stdout = json.dumps(report) if fault != "json" else "not json"
        if fault == "timeout":
            run.side_effect = subprocess.TimeoutExpired("probe", 10)
        if fault == "exit":
            run.side_effect = subprocess.CalledProcessError(2, "probe")
        with pytest.raises((ValueError, subprocess.SubprocessError)):
            prepare_launch(root, lock, digest)


def test_real_core_version_must_satisfy_both_constraints():
    """Different compatible ranges work only with a concrete observed version."""
    figma = replace(adapter(), dcc_mcp_core=">=0.20.44,<0.21")
    assert not negotiate(runtime(), figma).accepted
    assert negotiate(runtime(), figma, core_version="0.20.44").accepted
    assert not negotiate(runtime(), figma, core_version="0.21.0").accepted
    assert not negotiate(runtime(), figma, core_version="invalid").accepted


def test_probe_script_reads_metadata_without_importing_adapter_or_pth(tmp_path):
    """Exercise the actual probe with the existing test interpreter, without installation."""
    site = tmp_path / "site"
    info = site / "inert_adapter-1.2.3.dist-info"
    info.mkdir(parents=True)
    (info / "METADATA").write_text("Name: inert-adapter\nVersion: 1.2.3\n")
    (site / "inert_adapter.py").write_text('raise RuntimeError("must not import")')
    (site / "inject.pth").write_text("import nonexistent_dangerous_pth\n")
    report = json.loads(
        subprocess.run(
            [sys.executable, "-I", "-S", "-B", "-c", _PROBE, str(site), "inert-adapter"],
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
            env={**__import__("os").environ, "PYTHONPATH": str(tmp_path / "poison")},
        ).stdout
    )
    assert report["versions"] == {"inert-adapter": "1.2.3"}
    assert report["python_version"] == ".".join(map(str, sys.version_info[:3]))
    assert not list(site.rglob("__pycache__"))


def test_cli_emits_plan_without_starting_adapter(monkeypatch, capsys):
    """The public CLI delegates to the same verification boundary."""
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "dcc-mcp-runtime",
            "prepare-launch",
            "staged-root",
            "lock.json",
            "--expected-lock-sha256",
            "a" * 64,
        ],
    )
    with patch(
        "dcc_mcp_runtime.cli.prepare_launch", return_value={"requires_confirmation": True}
    ) as prepare:
        assert main() == 0
    prepare.assert_called_once_with("staged-root", "lock.json", "a" * 64)
    assert json.loads(capsys.readouterr().out)["requires_confirmation"]


@pytest.mark.parametrize("args", [["serve", "--bridge-port", "19061"], []])
def test_pinned_entry_arguments_survive_launch_planning(tmp_path, args):
    """Figma requires serve; argv must preserve exact tokens without shell interpretation."""
    root, lock, _, report = bundle(tmp_path)
    data = json.loads(lock.read_text())
    data["entry_args"] = args
    lock.write_text(json.dumps(data))
    digest = hashlib.sha256(lock.read_bytes()).hexdigest()
    with patch("dcc_mcp_runtime.launch.subprocess.run") as run:
        run.return_value.stdout = json.dumps(report)
        plan = prepare_launch(root, lock, digest)
    assert plan["argv"][8:] == args


@pytest.mark.parametrize("args", ["serve", [None], ["serve\x00"], ["{project}"]])
def test_invalid_entry_arguments_stop_before_probe(tmp_path, args):
    """Malformed argv cannot reach process creation."""
    root, lock, _, _ = bundle(tmp_path)
    data = json.loads(lock.read_text())
    data["entry_args"] = args
    lock.write_text(json.dumps(data))
    digest = hashlib.sha256(lock.read_bytes()).hexdigest()
    with patch("dcc_mcp_runtime.launch.subprocess.run") as run:
        with pytest.raises(ValueError):
            prepare_launch(root, lock, digest)
        run.assert_not_called()


def test_launch_bootstrap_preserves_module_arguments_without_shell(tmp_path):
    """Run an inert stand-in CLI, never the adapter, to verify runpy argv handling."""
    (tmp_path / "inert_cli.py").write_text("import sys,json; print(json.dumps(sys.argv[1:]))")
    args = ["serve", "--bridge-port", "19061", "literal;echo no-shell"]
    result = subprocess.run(
        [sys.executable, "-I", "-S", "-B", "-c", _LAUNCH, str(tmp_path), "inert_cli", *args],
        capture_output=True,
        text=True,
        check=True,
        timeout=10,
    )
    assert json.loads(result.stdout) == args
