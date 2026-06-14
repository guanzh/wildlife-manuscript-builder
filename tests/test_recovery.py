"""Tests for RecoveryManager — run schema + events.jsonl validation."""

from __future__ import annotations

import json
import yaml
from pathlib import Path

from wmb.core.recovery import RecoveryManager


class _MockProject:
    def __init__(self, tmp_path: Path) -> None:
        wmb_dir = tmp_path / ".wmb"
        wmb_dir.mkdir(parents=True, exist_ok=True)
        self.paths = type("Paths", (), {"wmb_dir": wmb_dir})()


def _write_yaml(path: Path, data) -> None:
    path.write_text(yaml.safe_dump(data), encoding="utf-8")


def _valid_run() -> dict:
    return {
        "run_id": "run-test",
        "status": "intake",
        "current_gate": "data_contract",
        "delivery_level": 0,
    }


def test_interrupted_running_task_becomes_retryable(tmp_path: Path) -> None:
    proj = _MockProject(tmp_path)
    run = _valid_run()
    run["status"] = "evidence_and_analysis"
    _write_yaml(proj.paths.wmb_dir / "run.yaml", run)
    # Write valid events.jsonl
    events_dir = proj.paths.wmb_dir / "logs"
    events_dir.mkdir(exist_ok=True)
    (events_dir / "events.jsonl").write_text(
        json.dumps({"event_id": "e1", "event_type": "transition"}) + "\n",
        encoding="utf-8",
    )
    (proj.paths.wmb_dir / "tasks").mkdir()
    _write_yaml(proj.paths.wmb_dir / "tasks" / "task-001.yaml", {
        "task_id": "task-001", "status": "running", "outputs": {},
    })
    mgr = RecoveryManager(proj)
    report = mgr.recover()
    assert len(report.retryable_tasks) == 1
    assert "task-001" in report.retryable_tasks


def test_unchanged_completed_task_is_skipped(tmp_path: Path) -> None:
    proj = _MockProject(tmp_path)
    run = _valid_run()
    run["status"] = "manuscript_drafting"
    _write_yaml(proj.paths.wmb_dir / "run.yaml", run)
    events_dir = proj.paths.wmb_dir / "logs"
    events_dir.mkdir(exist_ok=True)
    (events_dir / "events.jsonl").write_text(
        json.dumps({"event_id": "e1", "event_type": "transition"}) + "\n",
        encoding="utf-8",
    )
    (proj.paths.wmb_dir / "tasks").mkdir()
    output_file = tmp_path / "results.md"
    output_file.write_text("results", encoding="utf-8")
    _write_yaml(proj.paths.wmb_dir / "tasks" / "task-done.yaml", {
        "task_id": "task-done", "status": "completed",
        "outputs": {"result": str(output_file)},
    })
    mgr = RecoveryManager(proj)
    report = mgr.recover()
    assert "task-done" in report.unchanged_completed_tasks


def test_changed_completed_artifact_blocks(tmp_path: Path) -> None:
    proj = _MockProject(tmp_path)
    run = _valid_run()
    run["status"] = "package_verification"
    _write_yaml(proj.paths.wmb_dir / "run.yaml", run)
    events_dir = proj.paths.wmb_dir / "logs"
    events_dir.mkdir(exist_ok=True)
    (events_dir / "events.jsonl").write_text(
        json.dumps({"event_id": "e1", "event_type": "transition"}) + "\n",
        encoding="utf-8",
    )
    (proj.paths.wmb_dir / "tasks").mkdir()
    (proj.paths.wmb_dir / "artifacts").mkdir(parents=True, exist_ok=True)
    output_file = tmp_path / "analysis.json"
    output_file.write_text('{"version": 1}', encoding="utf-8")
    _write_yaml(proj.paths.wmb_dir / "tasks" / "task-anal.yaml", {
        "task_id": "task-anal", "status": "completed",
        "outputs": {"result": str(output_file)},
    })
    lock = proj.paths.wmb_dir / "artifacts" / "task-anal_output_hash.json"
    lock.write_text(json.dumps({str(output_file): "old_mtime"}), encoding="utf-8")
    mgr = RecoveryManager(proj)
    report = mgr.recover()
    assert report.blocked is True
    assert any("changed" in i.lower() for i in report.issues)


def test_corrupt_run_file_blocks(tmp_path: Path) -> None:
    proj = _MockProject(tmp_path)
    (proj.paths.wmb_dir / "run.yaml").write_text(": invalid yaml [", encoding="utf-8")
    mgr = RecoveryManager(proj)
    report = mgr.recover()
    assert report.blocked is True


def test_illegal_run_status_blocks(tmp_path: Path) -> None:
    """R5: Illegal run status must block recovery."""
    proj = _MockProject(tmp_path)
    _write_yaml(proj.paths.wmb_dir / "run.yaml", {
        "run_id": "run-bad",
        "status": "made_up_status",  # not in _LEGAL_STATUSES
        "current_gate": "unknown",
        "delivery_level": 0,
    })
    (proj.paths.wmb_dir / "logs").mkdir(parents=True, exist_ok=True)
    (proj.paths.wmb_dir / "logs" / "events.jsonl").write_text(
        json.dumps({"event_id": "e1"}) + "\n",
        encoding="utf-8",
    )
    mgr = RecoveryManager(proj)
    report = mgr.recover()
    assert report.blocked is True
    assert len(report.issues) > 0


def test_missing_events_jsonl_for_non_intake_blocks(tmp_path: Path) -> None:
    """R5: Non-intake must have events.jsonl."""
    proj = _MockProject(tmp_path)
    _write_yaml(proj.paths.wmb_dir / "run.yaml", {
        "run_id": "run-noev",
        "status": "evidence_and_analysis",
        "current_gate": "analysis",
        "delivery_level": 1,
    })
    mgr = RecoveryManager(proj)
    report = mgr.recover()
    assert report.blocked is True


def test_repeated_recovery_idempotent(tmp_path: Path) -> None:
    proj = _MockProject(tmp_path)
    run = _valid_run()
    _write_yaml(proj.paths.wmb_dir / "run.yaml", run)
    mgr = RecoveryManager(proj)
    r1 = mgr.recover()
    r2 = mgr.recover()
    assert r1.blocked == r2.blocked
