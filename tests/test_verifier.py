"""Tests for PackageVerifier with real claim trace validation."""

from __future__ import annotations

from pathlib import Path

import yaml

from wmb.core.verifier import PackageVerifier
from wmb.core.provenance import ProvenanceStore


class _MockProject:
    def __init__(self, tmp_path: Path) -> None:
        wmb_dir = tmp_path / ".wmb"
        wmb_dir.mkdir(parents=True, exist_ok=True)
        self.paths = type("Paths", (), {"wmb_dir": wmb_dir})()


def test_placeholder_author_caps_max_at_level_3(tmp_path: Path) -> None:
    proj = _MockProject(tmp_path)
    verifier = PackageVerifier(proj)
    report = verifier.verify(author={"name": "Dr. Who"})
    assert report.maximum_level <= 3
    assert any("PLACEHOLDER_AUTHOR" == f.code for f in report.findings)


def test_invalid_claim_file_does_not_grant_level4(tmp_path: Path) -> None:
    """R4: Just having a claim file is NOT enough for Level 4."""
    proj = _MockProject(tmp_path)
    # Create a claim file but not a valid trace
    claims_dir = proj.paths.wmb_dir / "artifacts" / "claims"
    claims_dir.mkdir(parents=True, exist_ok=True)
    (claims_dir / "bad_claim.yaml").write_text(yaml.safe_dump({
        "claim_id": "bad", "central": True,
    }), encoding="utf-8")

    report = PackageVerifier(proj).verify(
        author={"name": "Real Author", "affiliations": ["University"]},
        package={"bilingual_title": "T", "bilingual_abstract": "A"},
    )
    # Should fail because claim has no analysis_id, no result_card
    assert report.maximum_level < 4
    assert any("CLAIM_TRACE_FAILED" == f.code for f in report.findings)


def test_validated_central_claim_enables_level4(tmp_path: Path) -> None:
    """R4: Only validated central claims can reach Level 4."""
    proj = _MockProject(tmp_path)
    store = ProvenanceStore(proj)
    # Create analysis record
    analysis_file = tmp_path / "data.csv"
    analysis_file.write_text("a,b,c\n1,2,3\n", encoding="utf-8")
    store.record_analysis({
        "analysis_id": "a-valid",
        "status": "successful",
        "file_path": str(analysis_file),
        "content_hash": store._hash_file(analysis_file),
    })
    # Create valid central claim trace
    store.record_claim_trace(
        analysis_id="a-valid",
        result_card="Table 1",
        manuscript_claim="Key finding validated",
        central=True,
    )

    report = PackageVerifier(proj).verify(
        author={"name": "Real Author", "affiliations": ["University"]},
        package={"bilingual_title": "T", "bilingual_abstract": "A"},
    )
    assert report.maximum_level >= 4, f"Expected level >=4, got {report.maximum_level}"


def test_failed_analysis_in_claim_prevents_level4(tmp_path: Path) -> None:
    """Invalid analysis prevents Level 4 via CLAIM_TRACE_FAILED."""
    proj = _MockProject(tmp_path)
    store = ProvenanceStore(proj)
    store.record_analysis({"analysis_id": "a-fail", "status": "failed"})
    store.record_claim_trace(
        analysis_id="a-fail", result_card="T1", manuscript_claim="C", central=True,
    )
    report = PackageVerifier(proj).verify(
        author={"name": "Author", "affiliations": ["Uni"]},
        package={"bilingual_title": "T", "bilingual_abstract": "A"},
    )
    assert report.maximum_level < 4


def test_heuristic_finding_does_not_block(tmp_path: Path) -> None:
    proj = _MockProject(tmp_path)
    report = PackageVerifier(proj).verify()
    for f in report.findings:
        assert f.kind == "deterministic"
