"""Tests for HermesAdapter (Durable Kanban)."""

from __future__ import annotations

import json
from subprocess import CompletedProcess

from wmb.adapters.hermes import HermesAdapter


class _FakeRunner:
    """Injected runner that does not create real Kanban tasks."""

    def __init__(self, returncode: int = 0, stderr: str = "") -> None:
        self.returncode = returncode
        self.stderr = stderr
        self.last_args: list[str] | None = None

    def __call__(self, args, **kwargs):
        self.last_args = args
        return CompletedProcess(args, self.returncode, b"", self.stderr.encode())


def test_hermes_uses_kanban_create_not_kanban_task() -> None:
    runner = _FakeRunner()
    adapter = HermesAdapter(runner)
    cmd = adapter.build_create_command({
        "task_id": "test-001",
        "capability": "manuscript_writer",
        "objective": "Write Methods",
        "workspace": "/tmp/test",
    })
    cmd_str = " ".join(cmd)
    assert "kanban create" in cmd_str
    assert "kanban task" not in cmd_str


def test_dependencies_become_parent() -> None:
    runner = _FakeRunner()
    adapter = HermesAdapter(runner)
    cmd = adapter.build_create_command(
        {"task_id": "test-002", "objective": "Write"},
        dependencies=["t_parent1", "t_parent2"],
    )
    assert "--parent" in cmd
    # Find all parent occurrences
    parent_idx = [i for i, a in enumerate(cmd) if a == "--parent"]
    assert len(parent_idx) == 2


def test_task_id_becomes_idempotency_key() -> None:
    runner = _FakeRunner()
    adapter = HermesAdapter(runner)
    cmd = adapter.build_create_command({
        "task_id": "analysis-007",
        "objective": "Analyze",
    })
    cmd_str = " ".join(cmd)
    assert "wmb-analysis-007" in cmd_str


def test_no_shell_string_used() -> None:
    runner = _FakeRunner()
    adapter = HermesAdapter(runner)
    cmd = adapter.build_create_command({
        "task_id": "test-003",
        "objective": "Test with spaces and 'quotes'",
    })
    # Verify every argument is a separate list element (not a shell string)
    for arg in cmd:
        assert isinstance(arg, str), f"Non-string arg: {arg!r}"
    # The command list should have more than 2 elements (not a simple string)
    assert len(cmd) > 4


def test_invalid_result_fails_contract_validation() -> None:
    adapter = HermesAdapter()
    result = adapter.ingest_result("not a dict")
    assert result.accepted is False
    assert result.errors is not None


def test_accepted_result_updates_only_execution_status() -> None:
    adapter = HermesAdapter()
    result = adapter.ingest_result({"task_id": "analysis-001", "status": "completed"})
    assert result.accepted is True
    assert result.task_updated is True


def test_neither_adapter_changes_gate_state() -> None:
    """Adapters may update task execution status but must not call
    StateStore.transition() or decide a Gate."""
    adapter = HermesAdapter()
    assert not hasattr(adapter, "evaluate_change")
    assert not hasattr(adapter, "transition")


def test_reconciling_same_result_idempotent() -> None:
    runner = _FakeRunner()
    adapter = HermesAdapter(runner)
    r1 = adapter.ingest_result({"task_id": "analysis-001", "status": "completed"})
    r2 = adapter.ingest_result({"task_id": "analysis-001", "status": "completed"})
    assert r1.accepted == r2.accepted
    assert r1.task_updated == r2.task_updated
