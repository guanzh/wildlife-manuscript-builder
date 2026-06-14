"""Tests for GateEngine with author+items queue structure."""

from __future__ import annotations

from pathlib import Path

import pytest

from wmb.core.gate_engine import (
    GateDecision,
    GateEngine,
    LOW_RISK_CATEGORIES,
    MAJOR_CATEGORIES,
)


class _MockProject:
    def __init__(self, tmp_path: Path) -> None:
        wmb_dir = tmp_path / ".wmb"
        wmb_dir.mkdir(parents=True, exist_ok=True)
        self.paths = type("Paths", (), {"wmb_dir": wmb_dir})()


def test_major_analysis_change_creates_pending_confirmation(tmp_path: Path) -> None:
    proj = _MockProject(tmp_path)
    engine = GateEngine(proj)
    decision = engine.evaluate_change({
        "change_type": "core_model",
        "summary": "Switch from GLMM to occupancy model",
    })
    assert decision.status == GateDecision.AWAITING_AUTHOR_CONFIRMATION
    assert decision.queue_item_id is not None
    items = engine.pending_confirmations()
    assert len(items) == 1


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


def test_queue_preserves_author_structure(tmp_path: Path) -> None:
    """R3: Queue must preserve author field when adding items."""
    proj = _MockProject(tmp_path)
    engine = GateEngine(proj)
    engine.evaluate_change({"change_type": "core_hypothesis", "summary": "Test"})
    import yaml
    queue_file = proj.paths.wmb_dir / "author_confirmation_queue.yaml"
    raw = yaml.safe_load(queue_file.read_text(encoding="utf-8"))
    assert isinstance(raw, dict), f"Queue should be a dict, got {type(raw)}"
    assert "author" in raw, "Queue must contain 'author' field"
    assert "items" in raw, "Queue must contain 'items' field"
    assert len(raw["items"]) == 1


def test_atomic_write_does_not_produce_corrupt(tmp_path: Path) -> None:
    """Written YAML must be parseable."""
    proj = _MockProject(tmp_path)
    engine = GateEngine(proj)
    engine.evaluate_change({"change_type": "core_hypothesis", "summary": "First"})
    import yaml
    queue_file = proj.paths.wmb_dir / "author_confirmation_queue.yaml"
    raw = queue_file.read_text(encoding="utf-8")
    parsed = yaml.safe_load(raw)
    assert isinstance(parsed, dict)
    assert len(parsed["items"]) == 1


def test_every_major_category_requires_confirmation(tmp_path: Path) -> None:
    proj = _MockProject(tmp_path)
    engine = GateEngine(proj)
    for cat in MAJOR_CATEGORIES:
        decision = engine.evaluate_change({"change_type": cat, "summary": f"test {cat}"})
        assert decision.status == GateDecision.AWAITING_AUTHOR_CONFIRMATION, f"{cat}"
    assert len(engine.pending_confirmations()) == len(MAJOR_CATEGORIES)


def test_pending_confirmations_empty_when_none(tmp_path: Path) -> None:
    proj = _MockProject(tmp_path)
    engine = GateEngine(proj)
    assert engine.pending_confirmations() == []


def test_clear_confirmation_removes_item(tmp_path: Path) -> None:
    proj = _MockProject(tmp_path)
    engine = GateEngine(proj)
    decision = engine.evaluate_change({"change_type": "core_model", "summary": "Switch"})
    engine.clear_confirmation(decision.queue_item_id)
    assert engine.pending_confirmations() == []


def test_author_not_overwritten_when_adding_items(tmp_path: Path) -> None:
    """R3: Adding items must not overwrite author field."""
    proj = _MockProject(tmp_path)
    engine = GateEngine(proj)
    # Add first item
    engine.evaluate_change({"change_type": "core_model", "summary": "A"})
    import yaml
    qfile = proj.paths.wmb_dir / "author_confirmation_queue.yaml"
    data = yaml.safe_load(qfile.read_text(encoding="utf-8"))
    assert data["author"] == "Dr. Who"
    # Add second item
    engine.evaluate_change({"change_type": "research_question", "summary": "B"})
    data2 = yaml.safe_load(qfile.read_text(encoding="utf-8"))
    assert data2["author"] == "Dr. Who"
    assert len(data2["items"]) == 2
