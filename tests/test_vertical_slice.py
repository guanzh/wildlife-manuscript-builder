"""End-to-end vertical slice: init → task → dispatch → result → evaluate → verify."""

from __future__ import annotations

import json
from pathlib import Path

from wmb.cli import main


def test_vertical_slice(tmp_path: Path, capsys):
    """R6: Full CLI end-to-end through real core."""
    project = tmp_path / "vslice"
    capsys.readouterr()

    rc = main(["init", str(project)])
    assert rc == 0
    capsys.readouterr()

    rc = main(["task", "create", str(project),
               "--capability", "manuscript_writer",
               "--objective", "Draft Methods section"])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    task_id = out["task_id"]

    # Persisted task file
    task_file = project / ".wmb" / "tasks" / f"{task_id}.yaml"
    assert task_file.exists()

    rc = main(["dispatch", str(project), task_id, "--platform", "hermes"])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert "kanban create" in out["command"]

    # Valid result
    result = {
        "task_id": task_id,
        "status": "completed",
        "artifacts": [".wmb/artifacts/methods.md"],
        "findings": [{"description": "TP=42, FN=3", "type": "metric", "severity": "info", "source": "analysis"}],
        "unresolved_issues": [],
        "recommended_transition": "PROCEED",
        "confidence": "high",
        "limitations": [],
        "failures": [],
        "exclusions": [],
        "skipped_work": [],
    }
    result_file = tmp_path / "result.json"
    result_file.write_text(json.dumps(result))
    rc = main(["result", "ingest", str(project), str(result_file), "--platform", "hermes"])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["status"] == "ok"
