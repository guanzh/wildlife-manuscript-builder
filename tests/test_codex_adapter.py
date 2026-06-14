"""Tests for CodexAdapter."""

from __future__ import annotations

from wmb.adapters.codex import CodexAdapter


def test_codex_packet_contains_complete_paths() -> None:
    adapter = CodexAdapter()
    task = {
        "task_id": "analysis-001",
        "capability": "manuscript_writer",
        "objective": "Draft Methods section",
        "task_contract_path": ".wmb/contracts/task.yaml",
        "result_contract_path": ".wmb/contracts/result.yaml",
    }
    packet = adapter.prepare_dispatch(task)
    assert packet.adapter == "codex"
    assert "Methods" in packet.objective
    assert packet.task_contract is not None


def test_codex_packet_has_isolation_metadata() -> None:
    adapter = CodexAdapter()
    reviewer_task = {
        "task_id": "review-001",
        "capability": "reviewer",
        "objective": "Review Methods section",
    }
    packet = adapter.prepare_dispatch(reviewer_task)
    assert packet.isolated_context is True

    writer_task = {
        "task_id": "write-001",
        "capability": "manuscript_writer",
        "objective": "Write Methods",
    }
    packet2 = adapter.prepare_dispatch(writer_task)
    assert packet2.isolated_context is False


def test_invalid_result_fails_contract_validation() -> None:
    adapter = CodexAdapter()
    result = adapter.ingest_result("not a dict")
    assert result.accepted is False
    assert result.errors is not None
    assert len(result.errors) > 0


def test_accepted_result_updates_only_execution_status() -> None:
    adapter = CodexAdapter()
    result = adapter.ingest_result({"task_id": "analysis-001", "status": "completed"})
    assert result.accepted is True
    assert result.task_updated is True
    assert adapter.last_result() is not None
    assert adapter.last_result()["task_id"] == "analysis-001"


def test_neither_adapter_changes_gate_state() -> None:
    """Adapters may update task execution status but must not call
    StateStore.transition() or decide a Gate. This test checks that
    the Codex adapter exposes no Gate-related methods."""
    adapter = CodexAdapter()
    assert not hasattr(adapter, "evaluate_change")
    assert not hasattr(adapter, "transition")
    assert not hasattr(adapter, "gate_engine")


def test_reconciling_same_result_idempotent() -> None:
    adapter = CodexAdapter()
    r1 = adapter.ingest_result({"task_id": "analysis-001", "status": "completed"})
    r2 = adapter.ingest_result({"task_id": "analysis-001", "status": "completed"})
    assert r1.accepted == r2.accepted
    assert r1.task_updated == r2.task_updated
