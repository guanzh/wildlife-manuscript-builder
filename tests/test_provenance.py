"""Tests for ProvenanceStore (analysis and claim traces)."""

from __future__ import annotations

from pathlib import Path

import pytest

from wmb.core.provenance import ProvenanceStore


class _MockProject:
    def __init__(self, tmp_path: Path) -> None:
        wmb_dir = tmp_path / ".wmb"
        wmb_dir.mkdir(parents=True, exist_ok=True)
        self.paths = type("Paths", (), {"wmb_dir": wmb_dir})()


def test_failed_analysis_rejected_as_evidence(tmp_path: Path) -> None:
    proj = _MockProject(tmp_path)
    store = ProvenanceStore(proj)
    aid = store.record_analysis({"analysis_id": "a-fail", "status": "failed"})
    cid = store.record_claim_trace(analysis_id=aid, manuscript_claim="Claim X", central=True)
    report = store.validate_claim_trace(cid)
    assert not report.valid
    assert any("failed" in i for i in report.issues)


def test_valid_analysis_supports_claim(tmp_path: Path) -> None:
    proj = _MockProject(tmp_path)
    store = ProvenanceStore(proj)
    aid = store.record_analysis({
        "analysis_id": "a-good", "status": "successful",
    })
    cid = store.record_claim_trace(
        analysis_id=aid, result_card="Table 1", manuscript_claim="Claim", central=True,
    )
    report = store.validate_claim_trace(cid)
    assert report.valid


def test_hash_mismatch_blocks(tmp_path: Path) -> None:
    proj = _MockProject(tmp_path)
    store = ProvenanceStore(proj)
    file_path = tmp_path / "data.csv"
    file_path.write_text("a,b,c\n1,2,3\n", encoding="utf-8")
    store.record_analysis({
        "analysis_id": "a-hash",
        "status": "successful",
        "file_path": str(file_path),
        "content_hash": "badbadbadbadbad1",
    })
    cid = store.record_claim_trace(analysis_id="a-hash", manuscript_claim="Test", central=True)
    report = store.validate_claim_trace(cid)
    assert not report.valid
    assert any("Hash" in i for i in report.issues)


def test_missing_result_card_blocks_central_claim(tmp_path: Path) -> None:
    proj = _MockProject(tmp_path)
    store = ProvenanceStore(proj)
    store.record_analysis({"analysis_id": "a", "status": "successful"})
    cid = store.record_claim_trace(analysis_id="a", manuscript_claim="C")
    # Claim is central, but we didn't pass central=True — should be ok
    cid2 = store.record_claim_trace(analysis_id="a", manuscript_claim="C2", central=True)
    report = store.validate_claim_trace(cid2)
    assert not report.valid
    assert any("result_card" in i for i in report.issues)


def test_missing_caption_trace_blocks_central_figure_claim(tmp_path: Path) -> None:
    proj = _MockProject(tmp_path)
    store = ProvenanceStore(proj)
    cid = store.record_claim_trace(
        figure_or_table_caption="Fig 1 caption", central=True,
    )
    report = store.validate_claim_trace(cid)
    assert not report.valid
    assert any("requires an analysis trace" in i for i in report.issues)


def test_non_central_narrative_claim_may_omit_figure_caption(tmp_path: Path) -> None:
    proj = _MockProject(tmp_path)
    store = ProvenanceStore(proj)
    cid = store.record_claim_trace(
        manuscript_claim="Narrative claim without analysis", central=False,
    )
    report = store.validate_claim_trace(cid)
    # Central=False — no requirement for analysis or caption trace
    # But without manuscript_claim either, it's still an issue
    assert report.valid is True


def test_repeated_identical_record_idempotent(tmp_path: Path) -> None:
    proj = _MockProject(tmp_path)
    store = ProvenanceStore(proj)
    payload = {"analysis_id": "dup", "status": "successful"}
    a1 = store.record_analysis(payload)
    a2 = store.record_analysis(payload)
    assert a1 == a2
    # Should still be one file
    files = list(store.analysis_dir.iterdir())
    assert len(files) == 1


def test_validate_all_central_claims(tmp_path: Path) -> None:
    proj = _MockProject(tmp_path)
    store = ProvenanceStore(proj)
    store.record_analysis({"analysis_id": "a1", "status": "successful"})
    store.record_claim_trace(
        analysis_id="a1", result_card="R1", manuscript_claim="C1", central=True,
    )
    store.record_claim_trace(manuscript_claim="C2", central=False)
    reports = store.validate_all_central_claims()
    assert len(reports) == 1  # only central claims
