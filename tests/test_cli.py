"""CLI unit tests for WMB commands."""

from __future__ import annotations

import json
from pathlib import Path

from wmb import __version__
from wmb.cli import main


def test_cli_help_surface(capsys):
    assert main(["--help"]) == 0
    assert "Wildlife Manuscript Builder" in capsys.readouterr().out


def test_cli_version_surface(capsys):
    assert main(["--version"]) == 0
    assert __version__ in capsys.readouterr().out


def test_cli_init(tmp_path: Path):
    project = tmp_path / "test_project"
    assert main(["init", str(project)]) == 0
    assert (project / ".wmb" / "run.yaml").exists()
    assert (project / ".wmb" / "event_log.yaml").exists()


def test_cli_status_before_init_returns_not_found(capsys, tmp_path: Path):
    project = tmp_path / "nonexistent"
    rc = main(["status", str(project)])
    assert rc == 0


def test_cli_status_after_init(capsys, tmp_path: Path):
    project = tmp_path / "test_status"
    main(["init", str(project)])
    capsys.readouterr()  # discard init output
    assert main(["status", str(project)]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["run_status"] == "intake"
    assert out["author_status"] == "Dr. Who"


def test_cli_task_create(capsys, tmp_path: Path):
    project = tmp_path / "test_task"
    main(["init", str(project)])
    capsys.readouterr()
    assert main(["task", "create", str(project), "--capability", "manuscript_writer", "--objective", "Draft Methods"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["status"] == "ok"
    assert out["task"]["capability"] == "manuscript_writer"


def test_cli_dispatch_hermes(capsys, tmp_path: Path):
    project = tmp_path / "test_dispatch"
    main(["init", str(project)])
    capsys.readouterr()
    assert main(["dispatch", str(project), "task-001", "--platform", "hermes"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["platform"] == "hermes"
    assert "kanban create" in out["command"]


def test_cli_dispatch_codex(capsys, tmp_path: Path):
    project = tmp_path / "test_dispatch_cx"
    main(["init", str(project)])
    capsys.readouterr()
    assert main(["dispatch", str(project), "task-001", "--platform", "codex"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["platform"] == "codex"
    assert out["packet"]["adapter"] == "codex"


def test_cli_change_evaluate_low_risk(capsys, tmp_path: Path):
    project = tmp_path / "test_change"
    main(["init", str(project)])
    capsys.readouterr()
    change_file = tmp_path / "change.json"
    change_file.write_text(json.dumps({"change_type": "claim_narrowing", "summary": "Narrow overclaim"}))
    rc = main(["change", "evaluate", str(project), str(change_file)])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert "auto_refine" in str(out["status"])


def test_cli_change_evaluate_major(capsys, tmp_path: Path):
    project = tmp_path / "test_change_major"
    main(["init", str(project)])
    capsys.readouterr()
    change_file = tmp_path / "change_major.json"
    change_file.write_text(json.dumps({"change_type": "core_model", "summary": "Switch model"}))
    rc = main(["change", "evaluate", str(project), str(change_file)])
    assert rc == 3  # author_confirmation exit code
    out = json.loads(capsys.readouterr().out)
    assert "queue_item_id" in out


def test_cli_result_ingest_missing_file(capsys, tmp_path: Path):
    project = tmp_path / "test_result"
    main(["init", str(project)])
    capsys.readouterr()
    fake = tmp_path / "nonexistent.json"
    rc = main(["result", "ingest", str(project), str(fake), "--platform", "hermes"])
    assert rc == 2


def test_cli_invalid_command_fails():
    rc = main(["nonexistent"])
    assert rc == 2


def test_python_m_wmb_help(capsys):
    """Simulate `python -m wmb --help`."""
    assert main(["--help"]) == 0
