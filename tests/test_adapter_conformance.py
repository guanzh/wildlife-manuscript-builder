"""Adapter conformance tests: both adapters preserve identical core policy."""

from __future__ import annotations

from wmb.adapters.codex import CodexAdapter
from wmb.adapters.hermes import HermesAdapter

SAMPLE_TASK = {
    "task_id": "test-conformance-001",
    "capability": "manuscript_writer",
    "objective": "Draft Methods",
}


def test_same_task_and_result_produce_same_recommended_transition() -> None:
    """Given the same task and valid result, both adapters should ingest
    identically."""
    codex = CodexAdapter()
    hermes = HermesAdapter()
    result = {"task_id": "test-conformance-001", "status": "completed"}

    cr = codex.ingest_result(result)
    hr = hermes.ingest_result(result)

    assert cr.accepted == hr.accepted
    assert cr.task_updated == hr.task_updated


def test_neither_adapter_changes_canonical_gate_state() -> None:
    """Adapters must not expose Gate or StateStore transition methods."""
    codex = CodexAdapter()
    hermes = HermesAdapter()

    for adapter in (codex, hermes):
        assert not hasattr(adapter, "evaluate_change")
        assert not hasattr(adapter, "transition")
        assert not hasattr(adapter, "gate_engine")


def test_repeated_ingestion_is_idempotent() -> None:
    """Both adapters produce the same ingest result for repeat calls."""
    codex = CodexAdapter()
    hermes = HermesAdapter()
    result = {"task_id": "test-idempotent", "status": "completed"}

    for adapter in (codex, hermes):
        r1 = adapter.ingest_result(result)
        r2 = adapter.ingest_result(result)
        assert r1.accepted == r2.accepted
        assert r1.task_updated == r2.task_updated


def test_both_adapters_reject_invalid_result() -> None:
    codex = CodexAdapter()
    hermes = HermesAdapter()
    for adapter in (codex, hermes):
        r = adapter.ingest_result("not a dict")
        assert r.accepted is False
        assert r.errors is not None
