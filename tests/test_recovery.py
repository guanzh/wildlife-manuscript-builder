"""Tests for RecoveryManager."""

from __future__ import annotations

import json
import yaml
from pathlib import Path

import pytest

from wmb.core.recovery import RecoveryManager, RecoveryBlocked


class _MockProject:
    def __init__(self, tmp_path: Path) -> None:
        wmb_dir = tmp_path / ".wmb"
        wmb_dir.mkdir(parents=True, exist_ok=True)
        self.paths = type("Paths", (), {"wmb_dir": wmb_dir})()


def _write_yaml(path: Path, data) -> None:
    path.write_text(yaml.safe_dump(data), encoding="utf-8")


def test_interrupted_running_task_becomes_retryable(tmp_path: Path) -> None:
    proj = _MockProject(tmp_path)
    _write_yaml(proj.paths.wmb_dir / "run.yaml", {"status": "running", "current_task": "task-001"})
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
    _write_yaml(proj.paths.wmb_dir / "run.yaml", {"status": "completed"})
    (proj.paths.wmb_dir / "tasks").mkdir()
    # Completed task with outputs that exist
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
    _write_yaml(proj.paths.wmb_dir / "run.yaml", {"status": "completed"})
    (proj.paths.wmb_dir / "tasks").mkdir()
    (proj.paths.wmb_dir / "artifacts").mkdir(parents=True, exist_ok=True)
    # Create an output file
    output_file = tmp_path / "analysis.json"
    output_file.write_text('{"version": 1}', encoding="utf-8")
    _write_yaml(proj.paths.wmb_dir / "tasks" / "task-anal.yaml", {
        "task_id": "task-anal", "status": "completed",
        "outputs": {"result": str(output_file)},
    })
    # Write previous hash lock
    lock = proj.paths.wmb_dir / "artifacts" / "task-anal_output_hash.json"
    lock.write_text(json.dumps({str(output_file): "old_mtime"}), encoding="utf-8")
    mgr = RecoveryManager(proj)
    report = mgr.recover()
    assert report.blocked is True
    assert any("changed outputs" in i for i in report.issues)


def test_corrupt_run_file_blocks(tmp_path: Path) -> None:
    proj = _MockProject(tmp_path)
    (proj.paths.wmb_dir / "run.yaml").write_text(": invalid yaml [", encoding="utf-8")
    mgr = RecoveryManager(proj)
    report = mgr.recover()
    assert report.blocked is True
    assert any("corrupt" in i.lower() or "run.yaml" in i for i in report.issues)


def test_missing_wmb_dir_blocks(tmp_path: Path) -> None:
    proj = _MockProject(tmp_path)
    import shutil
    shutil.rmtree(proj.paths.wmb_dir)
    mgr = RecoveryManager(proj)
    report = mgr.recover()
    assert report.blocked is True
    assert any(".wmb" in i for i in report.issues)


def test_adapter_mismatch_reported(tmp_path: Path) -> None:
    proj = _MockProject(tmp_path)
    _write_yaml(proj.paths.wmb_dir / "run.yaml", {"status": "intake"})
    # Write saved adapter state
    _write_yaml(proj.paths.wmb_dir / "adapter_state.yaml", {"platform": "codex", "version": "1"})
    # Pass differing real state
    mgr = RecoveryManager(proj)
    report = mgr.recover(adapter_state={"platform": "hermes", "version": "2"})
    assert len(report.adapter_mismatches) > 0


def test_repeated_recovery_idempotent(tmp_path: Path) -> None:
    proj = _MockProject(tmp_path)
    _write_yaml(proj.paths.wmb_dir / "run.yaml", {"status": "intake"})
    mgr = RecoveryManager(proj)
    r1 = mgr.recover()
    r2 = mgr.recover()
    assert r1.blocked == r2.blocked
    assert len(r1.issues) == len(r2.issues)


def test_never_invents_gate_decision(tmp_path: Path) -> None:
    """RecoveryManager must not have evaluate_change or transition methods."""
    proj = _MockProject(tmp_path)
    _write_yaml(proj.paths.wmb_dir / "run.yaml", {"status": "intake"})
    mgr = RecoveryManager(proj)
    assert not hasattr(mgr, "evaluate_change")
    assert not hasattr(mgr, "transition")
    assert not hasattr(mgr, "gate_engine")
