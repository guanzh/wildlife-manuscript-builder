"""Tests for PackageVerifier."""

from __future__ import annotations

from pathlib import Path

import yaml

from wmb.core.verifier import PackageVerifier


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


def test_confirmed_metadata_can_reach_candidate_level_4(tmp_path: Path) -> None:
    proj = _MockProject(tmp_path)
    # Create claim traces so MISSING_CLAIM_TRACE doesn't block
    claims_dir = proj.paths.wmb_dir / "artifacts" / "claims"
    claims_dir.mkdir(parents=True, exist_ok=True)
    (claims_dir / "c1.yaml").write_text(yaml.safe_dump({
        "claim_id": "c1", "central": True, "manuscript_claim": "Test",
    }), encoding="utf-8")

    report = verifier = PackageVerifier(proj).verify(
        author={"name": "Real Author", "affiliations": ["University"]},
        package={"bilingual_title": "Title", "bilingual_abstract": "Abstract"},
    )
    assert report.maximum_level >= 4


def test_heuristic_weakness_does_not_block(tmp_path: Path) -> None:
    proj = _MockProject(tmp_path)
    verifier = PackageVerifier(proj)
    findings = verifier.verify().findings
    # All findings should be deterministic if they block
    for f in findings:
        assert f.kind == "deterministic"


def test_deterministic_failure_blocks(tmp_path: Path) -> None:
    proj = _MockProject(tmp_path)
    verifier = PackageVerifier(proj)
    # Create a failed analysis to trigger FAILED_ANALYSIS_CITED
    analysis_dir = proj.paths.wmb_dir / "artifacts" / "analysis"
    analysis_dir.mkdir(parents=True, exist_ok=True)
    (analysis_dir / "bad.yaml").write_text(yaml.safe_dump({
        "analysis_id": "bad", "status": "failed",
    }), encoding="utf-8")

    report = verifier.verify()
    assert report.blocking


def test_missing_claim_trace_blocks(tmp_path: Path) -> None:
    proj = _MockProject(tmp_path)
    verifier = PackageVerifier(proj)
    report = verifier.verify(
        author={"name": "Author", "affiliations": ["Uni"]},
        package={"bilingual_title": "T", "bilingual_abstract": "A"},
    )
    assert any("MISSING_CLAIM_TRACE" == f.code for f in report.findings)
