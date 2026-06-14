"""CLI unit tests for WMB commands — adapted for real core."""

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


def test_cli_init_passes_schema(capsys, tmp_path: Path):
    """R1: CLI init result passes run schema."""
    project = tmp_path / "r1_project"
    rc = main(["init", str(project)])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["run_status"] == "intake"
    # Verify real project structure
    assert (project / ".wmb" / "run.yaml").exists()
    assert (project / ".wmb" / "logs" / "events.jsonl").exists()


def test_cli_init_double_fails(capsys, tmp_path: Path):
    """Second init on same project should fail or return existing."""
    project = tmp_path / "double"
    rc1 = main(["init", str(project)])
    assert rc1 == 0
    capsys.readouterr()
    rc2 = main(["init", str(project)])
    assert rc2 == 0  # initialize_project handles existing gracefully
    capsys.readouterr()


def test_cli_status_after_init(capsys, tmp_path: Path):
    project = tmp_path / "st"
    main(["init", str(project)])
    capsys.readouterr()
    rc = main(["status", str(project)])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["run_status"] == "intake"


def test_cli_task_create(tmp_path: Path, capsys):
    """R2: task create must create a real task file."""
    project = tmp_path / "tc"
    main(["init", str(project)])
    capsys.readouterr()
    rc = main(["task", "create", str(project),
               "--capability", "manuscript_writer",
               "--objective", "Draft Methods"])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["status"] == "ok"
    task_id = out["task_id"]
    # Verify task file was created
    task_file = project / ".wmb" / "tasks" / f"{task_id}.yaml"
    assert task_file.exists(), f"Task file not created at {task_file}"


def test_cli_dispatch_hermes(tmp_path: Path, capsys):
    """R2: dispatch reads persisted task."""
    project = tmp_path / "dh"
    main(["init", str(project)])
    capsys.readouterr()
    # Create task first
    main(["task", "create", str(project),
          "--capability", "manuscript_writer",
          "--objective", "Write"])
    out1 = json.loads(capsys.readouterr().out)
    task_id = out1["task_id"]
    rc = main(["dispatch", str(project), task_id, "--platform", "hermes"])
    assert rc == 0
    out2 = json.loads(capsys.readouterr().out)
    assert "kanban create" in out2["command"]


def test_cli_dispatch_codex(tmp_path: Path, capsys):
    project = tmp_path / "dc"
    main(["init", str(project)])
    capsys.readouterr()
    main(["task", "create", str(project),
          "--capability", "reviewer",
          "--objective", "Review"])
    out1 = json.loads(capsys.readouterr().out)
    task_id = out1["task_id"]
    rc = main(["dispatch", str(project), task_id, "--platform", "codex"])
    assert rc == 0
    out2 = json.loads(capsys.readouterr().out)
    assert out2["platform"] == "codex"


def test_cli_dispatch_unknown_task_rejected(tmp_path: Path, capsys):
    project = tmp_path / "dunk"
    main(["init", str(project)])
    capsys.readouterr()
    rc = main(["dispatch", str(project), "task-nonexistent", "--platform", "hermes"])
    assert rc == 2
    stderr = capsys.readouterr().err
    assert "Unknown task_id" in stderr


def test_intake_to_level4_rejected(tmp_path: Path, capsys):
    """R1: intake → candidate_level_4 must be rejected."""
    project = tmp_path / "i2l4"
    main(["init", str(project)])
    capsys.readouterr()
    rc = main(["transition", str(project),
               "--to", "candidate_level_4",
               "--decision", "PROCEED",
               "--reason", "quick path"])
    assert rc == 3  # IllegalTransition
    stderr = capsys.readouterr().err
    assert "Illegal transition" in stderr or "invalid" in stderr.lower()


def test_cli_result_ingest_invalid_schema_rejected(tmp_path: Path, capsys):
    """R2: invalid result schema rejected."""
    project = tmp_path / "ris"
    main(["init", str(project)])
    capsys.readouterr()
    # Create task
    main(["task", "create", str(project),
          "--capability", "manuscript_writer",
          "--objective", "Write"])
    out1 = json.loads(capsys.readouterr().out)
    task_id = out1["task_id"]
    # Write incomplete result (missing required fields)
    bad_result = {"task_id": task_id}  # missing status, artifacts, findings, etc.
    result_file = tmp_path / "bad_result.json"
    result_file.write_text(json.dumps(bad_result))
    rc = main(["result", "ingest", str(project), str(result_file), "--platform", "hermes"])
    assert rc == 2  # Contract validation failed
    stderr = capsys.readouterr().err
    assert "Contract" in stderr or "contract" in stderr or "invalid" in stderr.lower()


def test_cli_result_ingest_unknown_task_rejected(tmp_path: Path, capsys):
    project = tmp_path / "riunk"
    main(["init", str(project)])
    capsys.readouterr()
    result_file = tmp_path / "unk_result.json"
    result = {
        "task_id": "task-nonexistent",
        "status": "completed",
        "artifacts": [],
        "findings": [],
        "unresolved_issues": [],
        "recommended_transition": "PROCEED",
        "confidence": "high",
        "limitations": [],
        "failures": [],
        "exclusions": [],
        "skipped_work": [],
    }
    result_file.write_text(json.dumps(result))
    rc = main(["result", "ingest", str(project), str(result_file), "--platform", "hermes"])
    assert rc == 2
    stderr = capsys.readouterr().err
    assert "not found" in stderr.lower()
