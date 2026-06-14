"""End-to-end vertical slice test for the first usable WMB workflow."""

from __future__ import annotations

import json
from pathlib import Path

from wmb.cli import main


def test_vertical_slice(tmp_path: Path, capsys):
    """Full pipeline: init → task → dispatch (dry) → result → ingest → evaluate."""
    project = tmp_path / "vslice"
    calls = []

    # 1. Initialize project
    rc = main(["init", str(project)])
    assert rc == 0
    assert (project / ".wmb" / "run.yaml").exists()
    capsys.readouterr()

    # 2. Create manuscript_writer task
    rc = main(["task", "create", str(project),
               "--capability", "manuscript_writer",
               "--objective", "Draft Methods section",
               "--output", ".wmb/artifacts/methods.md"])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["status"] == "ok"
    task_id = out["task_id"]
    calls.append(("task_create", out))

    # 3. Prepare Hermes command without execution
    rc = main(["dispatch", str(project), task_id, "--platform", "hermes"])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["platform"] == "hermes"
    assert "kanban create" in out["command"]
    assert "note" in out  # dry-run note
    calls.append(("dispatch_hermes", out))

    # 4. Write valid structured result
    result_file = tmp_path / "result.json"
    result = {
        "task_id": task_id,
        "status": "completed",
        "output_path": ".wmb/artifacts/methods.md",
        "findings": [],
    }
    result_file.write_text(json.dumps(result))

    # 5. Ingest result
    rc = main(["result", "ingest", str(project), str(result_file), "--platform", "hermes"])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["status"] == "ok"
    assert out["task_updated"] is True
    calls.append(("ingest_result", out))

    # 6. Evaluate low-risk claim narrowing
    change_file = tmp_path / "change_low_risk.json"
    change_file.write_text(json.dumps({
        "change_type": "claim_narrowing",
        "summary": "Narrow unsupported overclaim",
    }))
    rc = main(["change", "evaluate", str(project), str(change_file)])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert "auto_refine" in str(out["status"])
    calls.append(("evaluate_low_risk", out))

    # 7. Confirm canonical run remains controlled by StateStore
    rc = main(["status", str(project)])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["run_status"] == "intake"  # unchanged by adapters/Gates
    calls.append(("status_check", out))

    # Summary
    assert len(calls) == 5, f"Expected 5 tracked steps, got {len(calls)}"
