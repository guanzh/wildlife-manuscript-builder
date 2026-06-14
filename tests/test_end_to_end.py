"""Full end-to-end acceptance test with real core."""

from __future__ import annotations

import json
import yaml
from pathlib import Path

from wmb.cli import main
from wmb.core.provenance import ProvenanceStore
from wmb.core.verifier import PackageVerifier


class _MockProject:
    def __init__(self, tmp_path: Path) -> None:
        wmb_dir = tmp_path / ".wmb"
        wmb_dir.mkdir(parents=True, exist_ok=True)
        self.paths = type("Paths", (), {"wmb_dir": wmb_dir})()


def _valid_result(task_id: str) -> dict:
    return {
        "task_id": task_id,
        "status": "completed",
        "artifacts": [],
        "findings": [{
            "description": "TP=42",
            "type": "metric",
            "severity": "info",
            "source": "analysis",
        }],
        "unresolved_issues": [],
        "recommended_transition": "PROCEED",
        "confidence": "high",
        "limitations": [],
        "failures": [],
        "exclusions": [],
        "skipped_work": [],
    }


def test_end_to_end_workflow(tmp_path: Path, capsys) -> None:
    """R10: Complete CLI + real core end-to-end."""
    project = tmp_path / "e2e"
    capsys.readouterr()

    # Init
    rc = main(["init", str(project)])
    assert rc == 0
    capsys.readouterr()

    # Create analysis task → file persists
    rc = main(["task", "create", str(project),
               "--capability", "manuscript_writer",
               "--objective", "Draft Methods"])
    assert rc == 0
    task_out = json.loads(capsys.readouterr().out)
    task_id = task_out["task_id"]
    task_file = project / ".wmb" / "tasks" / f"{task_id}.yaml"
    assert task_file.exists()

    # Dispatch (dry-run)
    rc = main(["dispatch", str(project), task_id, "--platform", "hermes"])
    assert rc == 0
    capsys.readouterr()

    # Ingest valid result
    result_file = tmp_path / "result.json"
    result_file.write_text(json.dumps(_valid_result(task_id)))
    rc = main(["result", "ingest", str(project), str(result_file), "--platform", "hermes"])
    assert rc == 0
    capsys.readouterr()

    # Record provenance + claim trace
    store = ProvenanceStore(_MockProject(project))
    analysis_file = tmp_path / "data.csv"
    analysis_file.write_text("a,b,c\n1,2,3\n", encoding="utf-8")
    aid = store.record_analysis({
        "analysis_id": "e2e-analysis",
        "status": "successful",
        "file_path": str(analysis_file),
        "content_hash": store._hash_file(analysis_file),
    })
    store.record_claim_trace(
        analysis_id=aid, result_card="Table 1",
        manuscript_claim="Validated finding", central=True,
    )

    # Verify — should show level < 4 because Dr. Who placeholder
    proj = _MockProject(project)
    report = PackageVerifier(proj).verify()
    assert report.maximum_level <= 3

    # Verify with author info + validated claims
    report2 = PackageVerifier(proj).verify(
        author={"name": "Real Author", "affiliations": ["University"]},
        package={"bilingual_title": "T", "bilingual_abstract": "A"},
    )
    assert report2.maximum_level >= 4

    # Gate engine preserves author in queue
    from wmb.core.gate_engine import GateEngine
    engine = GateEngine(_MockProject(project))
    engine.evaluate_change({"change_type": "core_model", "summary": "Switch model"})
    queue_file = project / ".wmb" / "author_confirmation_queue.yaml"
    qdata = yaml.safe_load(queue_file.read_text(encoding="utf-8"))
    assert "author" in qdata
    assert len(qdata["items"]) > 0
