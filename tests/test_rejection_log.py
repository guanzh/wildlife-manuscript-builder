"""Tests for RejectionLedger."""

from __future__ import annotations

from pathlib import Path

import pytest

from wmb.core.logging import RejectionLedger, VALID_ACTIONS


class _MockProject:
    def __init__(self, tmp_path: Path) -> None:
        wmb_dir = tmp_path / ".wmb"
        wmb_dir.mkdir(parents=True, exist_ok=True)
        self.paths = type("Paths", (), {"wmb_dir": wmb_dir})()


def test_ledger_records_all_allowed_actions(tmp_path: Path) -> None:
    proj = _MockProject(tmp_path)
    ledger = RejectionLedger(proj)
    for action in sorted(VALID_ACTIONS):
        eid = ledger.record(action, f"test {action}")
        assert eid.startswith("rj_")
    assert len(ledger.entries()) == len(VALID_ACTIONS)


def test_blank_reason_raises(tmp_path: Path) -> None:
    proj = _MockProject(tmp_path)
    ledger = RejectionLedger(proj)
    with pytest.raises(ValueError, match="must be non-empty"):
        ledger.record("failed", "")


def test_invalid_action_raises(tmp_path: Path) -> None:
    proj = _MockProject(tmp_path)
    ledger = RejectionLedger(proj)
    with pytest.raises(ValueError, match="Invalid rejection action"):
        ledger.record("made_up_action", "test")


def test_concurrent_appends_remain_valid_jsonl(tmp_path: Path) -> None:
    proj = _MockProject(tmp_path)
    # Simulate two instances appending concurrently
    ledger1 = RejectionLedger(proj)
    ledger2 = RejectionLedger(proj)
    ids = [
        ledger1.record("failed", "concurrent A"),
        ledger2.record("skipped", "concurrent B"),
        ledger1.record("retried", "concurrent C"),
    ]
    all_entries = ledger1.entries()
    assert len(all_entries) == 3
    saved_ids = [e["entry_id"] for e in all_entries]
    for eid in ids:
        assert eid in saved_ids


def test_ledger_metadata_is_stored(tmp_path: Path) -> None:
    proj = _MockProject(tmp_path)
    ledger = RejectionLedger(proj)
    meta = {"source": "test", "original_claim": "H0"}
    ledger.record("dropped_claim", "Removed unsupported claim", metadata=meta)
    entries = ledger.entries()
    assert entries[0]["metadata"]["source"] == "test"


def test_empty_ledger_returns_empty_list(tmp_path: Path) -> None:
    proj = _MockProject(tmp_path)
    ledger = RejectionLedger(proj)
    assert ledger.entries() == []


def test_entry_has_required_fields(tmp_path: Path) -> None:
    proj = _MockProject(tmp_path)
    ledger = RejectionLedger(proj)
    ledger.record("excluded", "Excluded outlier site")
    entry = ledger.entries()[0]
    assert "entry_id" in entry
    assert "action" in entry
    assert "summary" in entry
    assert "metadata" in entry
