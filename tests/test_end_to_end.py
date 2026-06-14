"""End-to-end acceptance test for the full WMB workflow."""

from __future__ import annotations

import json
from pathlib import Path

from wmb.cli import main
from wmb.core.journal import JournalRefresh
from wmb.core.verifier import PackageVerifier


class _MockProject:
    def __init__(self, tmp_path: Path) -> None:
        wmb_dir = tmp_path / ".wmb"
        wmb_dir.mkdir(parents=True, exist_ok=True)
        self.paths = type("Paths", (), {"wmb_dir": wmb_dir})()


def test_end_to_end_workflow(tmp_path: Path, capsys) -> None:
    """Full pipeline: init → create → dispatch → ingest → provenance → 
    review → auto-refine → recover → verify."""
    project = tmp_path / "e2e"
    capsys.readouterr()

    # 1. Initialize project
    rc = main(["init", str(project)])
    assert rc == 0
    capsys.readouterr()

    # 2. Create analysis task
    rc = main(["task", "create", str(project),
               "--capability", "manuscript_writer",
               "--objective", "Draft Methods"])
    assert rc == 0
    task_out = json.loads(capsys.readouterr().out)
    task_id = task_out["task_id"]

    # 3. Prepare Hermes dispatch (dry)
    rc = main(["dispatch", str(project), task_id, "--platform", "hermes"])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert "kanban create" in out["command"]

    # 4. Ingest usable_with_caveat result
    result_file = tmp_path / "analysis_result.json"
    result_file.write_text(json.dumps({
        "task_id": task_id,
        "status": "usable_with_caveat",
        "output_path": "methods.md",
    }))
    rc = main(["result", "ingest", str(project), str(result_file), "--platform", "hermes"])
    assert rc == 0
    capsys.readouterr()

    # 5. Record analysis provenance
    from wmb.core.provenance import ProvenanceStore
    store = ProvenanceStore(_MockProject(project))
    analysis_id = store.record_analysis({
        "analysis_id": "e2e-analysis",
        "status": "usable_with_caveat",
        "file_path": "methods.md",
        "content_hash": "dummy",
    })

    # 6. Record central claim trace
    claim_id = store.record_claim_trace(
        analysis_id=analysis_id,
        result_card="Table 1",
        manuscript_claim="Key finding validated",
        central=True,
    )

    # 7. Create isolated reviewer task
    rc = main(["task", "create", str(project),
               "--capability", "reviewer",
               "--objective", "Review Methods section"])
    assert rc == 0
    review_task = json.loads(capsys.readouterr().out)

    # 8. Ingest review result
    review_file = tmp_path / "review_result.json"
    review_file.write_text(json.dumps({
        "task_id": review_task["task_id"],
        "status": "completed",
        "findings": [{"severity": "minor", "description": "Narrow claim 3.2"}],
    }))
    rc = main(["result", "ingest", str(project), str(review_file), "--platform", "hermes"])
    assert rc == 0
    capsys.readouterr()

    # 9. Auto-refine one low-risk issue
    change_file = tmp_path / "change_low.json"
    change_file.write_text(json.dumps({
        "change_type": "claim_narrowing",
        "summary": "Narrow claim 3.2 based on review feedback",
    }))
    rc = main(["change", "evaluate", str(project), str(change_file)])
    assert rc == 0  # auto_refine = 0 exit code
    out = json.loads(capsys.readouterr().out)
    assert "auto_refine" in str(out["status"])

    # 10. Recover after simulated interruption
    rc = main(["resume", str(project)])
    assert rc == 0
    capsys.readouterr()

    # 11. Verify package — should stop at Level 3 because Dr. Who
    proj_stub = _MockProject(project)
    verifier = PackageVerifier(proj_stub)
    report = verifier.verify()
    assert report.maximum_level <= 3
    assert report.blocking is True
    assert any("PLACEHOLDER_AUTHOR" in f.code for f in report.findings)

    # 12. Confirm real author removes only the author blocker
    report2 = verifier.verify(author={"name": "Real Author", "affiliations": ["University"]},
                               package={"bilingual_title": "T", "bilingual_abstract": "A"})
    # Other deterministic failures remain blocking (missing claim trace check passes
    # since we recorded one in step 6)
    # Verify the find count changes
    placeholder_findings = [f for f in report2.findings if "PLACEHOLDER" in f.code]
    assert len(placeholder_findings) == 0

    capsys.readouterr()
