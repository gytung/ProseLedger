"""Publication boundaries: resources, portable configuration, and input validation."""

from copy import deepcopy
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from proseledger import pipeline, runner
from proseledger.codex_client import CodexCLIError, CodexCLIModel
from proseledger import processes


def test_resource_verification_never_constructs_a_model(monkeypatch):
    def fail(*args, **kwargs):
        raise AssertionError("Resource validation must not instantiate a model.")

    monkeypatch.setattr(CodexCLIModel, "__init__", fail)
    result = runner.verify_runtime()
    assert result["status"] == "passed"
    assert result["new_model_calls"] == 0
    assert result["memory_cards"] == 5


def test_changed_resource_is_rejected_before_a_run(tmp_path, monkeypatch):
    content = b"fixed input"
    (tmp_path / "input.txt").write_bytes(content)
    (tmp_path / "integrity.json").write_text(
        json.dumps({"files": {"input.txt": hashlib.sha256(content).hexdigest()}})
    )
    monkeypatch.setattr(runner, "DATA", tmp_path)
    runner.verify_resources()
    (tmp_path / "input.txt").write_bytes(b"modified input")
    with pytest.raises(ValueError, match="resource differs"):
        runner.verify_resources()


def test_source_release_does_not_claim_archived_replay(tmp_path):
    with pytest.raises(ValueError, match="fresh generation only"):
        runner.execute(tmp_path / "run", mode="saved_demo")


def test_input_contract_rejects_a_different_model_before_calls(tmp_path):
    with pytest.raises(ValueError, match="fixes the model"):
        runner.execute(tmp_path / "run", model="a-different-model")


def test_portable_cli_override_is_probed_without_credentials(tmp_path, monkeypatch):
    binary = tmp_path / ("codex.exe" if processes.os.name == "nt" else "codex")
    binary.write_bytes(b"not executable: subprocess is mocked")
    monkeypatch.setenv("PROSELEDGER_CODEX_PATH", str(binary))
    observed = []

    def run(command, **kwargs):
        observed.append((command, kwargs))
        return SimpleNamespace(returncode=0, stdout="codex-cli test\n")

    monkeypatch.setattr(processes.subprocess, "run", run)
    assert processes.find_codex(CodexCLIModel, None) == str(binary)
    assert observed[0][0] == [str(binary), "--version"]
    assert "OPENAI_API_KEY" not in observed[0][1]["env"]


def test_invalid_explicit_cli_override_does_not_silently_fallback(tmp_path, monkeypatch):
    monkeypatch.setenv("PROSELEDGER_CODEX_PATH", str(tmp_path / "missing"))
    with pytest.raises(CodexCLIError, match="PROSELEDGER_CODEX_PATH"):
        processes.find_codex(CodexCLIModel, None)


def test_local_pdf_provenance_cannot_escape_source_folder(tmp_path):
    sources = deepcopy(pipeline.load_sources(runner.DATA / "sources.json")[:2])
    digest = "a" * 64
    sources[0].update(
        url=f"local-pdf://sha256/{digest}", pdf_sha256=digest, pdf_file="../private.pdf"
    )
    path = tmp_path / "sources.json"
    path.write_text(json.dumps(sources))
    with pytest.raises(ValueError, match="relative"):
        pipeline.load_sources(path)
