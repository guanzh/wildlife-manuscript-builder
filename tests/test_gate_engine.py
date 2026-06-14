"""Tests for GateEngine and author-confirmation queue."""

from __future__ import annotations

from pathlib import Path

import pytest

from wmb.core.gate_engine import (
    GateDecision,
    GateEngine,
    LOW_RISK_CATEGORIES,
    MAJOR_CATEGORIES,
)


# ---- helpers ----

class _MockProject:
    """Minimal project stub with .paths.wmb_dir."""

    def __init__(self, tmp_path: Path) -> None:
        wmb_dir = tmp_path / ".wmb"
        wmb_dir.mkdir(parents=True, exist_ok=True)
        self.paths = type("Paths", (), {"wmb_dir": wmb_dir})()


# ---- tests ----

def test_major_analysis_change_creates_pending_confirmation(tmp_path: Path) -> None:
    proj = _MockProject(tmp_path)
    engine = GateEngine(proj)
    decision = engine.evaluate_change({
        "change_type": "core_model",
        "summary": "Switch from GLMM to occupancy model",
    })
    assert decision.status == GateDecision.AWAITING_AUTHOR_CONFIRMATION
    assert decision.queue_item_id is not None
    # exactly one pending item
    assert len(engine.pending_confirmations()) == 1


def test_repeated_identical_major_change_does_not_duplicate(tmp_path: Path) -> None:
    proj = _MockProject(tmp_path)
    engine = GateEngine(proj)
    d1 = engine.evaluate_change({
        "change_type": "research_question",
        "summary": "Change to habitat connectivity",
    })
    d2 = engine.evaluate_change({
        "change_type": "research_question",
        "summary": "Change to habitat connectivity",
    })
    assert d1.queue_item_id == d2.queue_item_id
    assert len(engine.pending_confirmations()) == 1


def test_low_risk_claim_narrowing_auto_refines(tmp_path: Path) -> None:
    proj = _MockProject(tmp_path)
    engine = GateEngine(proj)
    for cat in LOW_RISK_CATEGORIES:
        decision = engine.evaluate_change({"change_type": cat, "summary": f"Auto {cat}"})
        assert decision.status == GateDecision.AUTO_REFINE, f"{cat} should auto-refine"
    assert len(engine.pending_confirmations()) == 0


def test_unknown_change_blocks(tmp_path: Path) -> None:
    proj = _MockProject(tmp_path)
    engine = GateEngine(proj)
    decision = engine.evaluate_change({
        "change_type": "completely_unknown_category",
        "summary": "test",
    })
    assert decision.status == GateDecision.BLOCKED_UNKNOWN_CHANGE


def test_empty_change_type_blocks(tmp_path: Path) -> None:
    proj = _MockProject(tmp_path)
    engine = GateEngine(proj)
    decision = engine.evaluate_change({"change_type": "", "summary": "empty"})
    assert decision.status == GateDecision.BLOCKED_UNKNOWN_CHANGE


def test_queue_write_failure_does_not_produce_corrupt_yaml(tmp_path: Path) -> None:
    proj = _MockProject(tmp_path)
    engine = GateEngine(proj)
    # Write a valid item first
    engine.evaluate_change({"change_type": "core_hypothesis", "summary": "First"})
    q = list(engine.pending_confirmations())
    assert len(q) == 1
    # Read raw YAML; it should be parseable
    import yaml
    raw = (proj.paths.wmb_dir / "author_confirmation_queue.yaml").read_text(encoding="utf-8")
    parsed = yaml.safe_load(raw)
    assert isinstance(parsed, list)
    assert len(parsed) == 1


def test_every_major_category_requires_confirmation(tmp_path: Path) -> None:
    proj = _MockProject(tmp_path)
    engine = GateEngine(proj)
    for cat in MAJOR_CATEGORIES:
        decision = engine.evaluate_change({"change_type": cat, "summary": f"test {cat}"})
        assert decision.status == GateDecision.AWAITING_AUTHOR_CONFIRMATION, f"{cat}"
    assert len(engine.pending_confirmations()) == len(MAJOR_CATEGORIES)


def test_pending_confirmations_returns_empty_list_when_none(tmp_path: Path) -> None:
    proj = _MockProject(tmp_path)
    engine = GateEngine(proj)
    assert engine.pending_confirmations() == []


def test_clear_confirmation_removes_item(tmp_path: Path) -> None:
    proj = _MockProject(tmp_path)
    engine = GateEngine(proj)
    decision = engine.evaluate_change({"change_type": "core_model", "summary": "Switch"})
    assert len(engine.pending_confirmations()) == 1
    engine.clear_confirmation(decision.queue_item_id)
    assert engine.pending_confirmations() == []


def test_clear_nonexistent_confirmation_returns_false(tmp_path: Path) -> None:
    proj = _MockProject(tmp_path)
    engine = GateEngine(proj)
    assert engine.clear_confirmation("nonexistent") is False
