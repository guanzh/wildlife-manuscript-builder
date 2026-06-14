"""Interruption recovery for WMB manuscript runs."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


_LEGAL_STATUSES = frozenset({
    "intake", "awaiting_research_direction", "evidence_and_analysis",
    "result_and_claim_build", "manuscript_drafting", "independent_review",
    "package_verification", "awaiting_final_confirmation",
    "candidate_level_4", "downgraded", "blocked",
})


class RecoveryBlocked(RuntimeError):
    """Raised when canonical run state is corrupt and cannot recover."""


@dataclass
class RecoveryReport:
    """Structured output from RecoveryManager.recover()."""
    blocked: bool = False
    retryable_tasks: list[str] = field(default_factory=list)
    tasks_to_rerun: list[str] = field(default_factory=list)
    unchanged_completed_tasks: list[str] = field(default_factory=list)
    adapter_mismatches: list[str] = field(default_factory=list)
    issues: list[str] = field(default_factory=list)


class RecoveryManager:
    """Analyse canonical state after interruption and recommend next steps.

    Never invents a Gate decision. Never silently reruns a completed
    task whose outputs have changed.
    """

    def __init__(self, project: Any) -> None:
        self._project = project

    @property
    def wmb_dir(self) -> Path:
        try:
            return self._project.paths.wmb_dir
        except AttributeError:
            return Path(getattr(self._project, "project", ".")) / ".wmb"

    # ----- main entry -----

    def recover(self, adapter_state: Any = None) -> RecoveryReport:
        """Analyse the project and return a RecoveryReport.

        Parameters
        ----------
        adapter_state:
            Optional injected adapter snapshot for mismatch detection.
        """
        report = RecoveryReport()
        wmb = self.wmb_dir
        if not wmb.is_dir():
            report.blocked = True
            report.issues.append(".wmb/ directory not found")
            return report

        # 1. Validate canonical run against run schema
        try:
            run_data = self._load_yaml(wmb / "run.yaml")
        except Exception as exc:
            report.blocked = True
            report.issues.append(f"Corrupt run.yaml: {exc}")
            return report
        if not isinstance(run_data, dict):
            report.blocked = True
            report.issues.append("run.yaml is not a valid mapping")
            return report

        # Validate run against schema
        try:
            from wmb.contracts import validate_contract
            validate_contract("run", run_data)
        except Exception as exc:
            report.blocked = True
            report.issues.append(f"Run schema validation failed: {exc}")
            return report

        # 2. Validate event history
        event_path = wmb / "logs" / "events.jsonl"
        if event_path.exists():
            try:
                lines = event_path.read_text(encoding="utf-8").strip().split("\n")
                for lineno, line in enumerate(lines, 1):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        import json as _json
                        _json.loads(line)
                    except Exception:
                        report.blocked = True
                        report.issues.append(f"Corrupt events.jsonl at line {lineno}")
                        return report
                # Legal run statuses check
                if run_data.get("status") not in _LEGAL_STATUSES:
                    report.blocked = True
                    report.issues.append(f"Illegal run status: {run_data.get('status')}")
                    return report
            except Exception as exc:
                report.blocked = True
                report.issues.append(f"Cannot read events.jsonl: {exc}")
                return report
        elif run_data.get("status") != "intake":
            # After intake, events.log must exist
            report.blocked = True
            report.issues.append("events.jsonl missing for non-intake run status")
            return report

        # 3. Scan tasks directory
        tasks_dir = wmb / "tasks"
        if tasks_dir.is_dir():
            for task_file in sorted(tasks_dir.iterdir()):
                if task_file.suffix not in (".yaml", ".json", ".yml"):
                    continue
                try:
                    task_data = self._load_yaml(task_file)
                except Exception as exc:
                    report.issues.append(f"Cannot parse task {task_file.name}: {exc}")
                    continue

                task_id = task_data.get("task_id", task_file.stem)
                task_status = task_data.get("status", "unknown")
                outputs = task_data.get("outputs", task_data.get("output", {}))

                if task_status == "running":
                    if self._has_valid_outputs(outputs, wmb):
                        report.tasks_to_rerun.append(task_id)
                    else:
                        report.retryable_tasks.append(task_id)

                elif task_status == "completed":
                    if self._outputs_changed(task_id, outputs, wmb):
                        report.blocked = True
                        report.issues.append(
                            f"Completed task {task_id} has changed outputs — "
                            "blocking until user confirms"
                        )
                    else:
                        report.unchanged_completed_tasks.append(task_id)

        # 4. Detect adapter mismatch
        if adapter_state is not None:
            try:
                mismatches = self._check_adapter_mismatch(adapter_state, wmb)
                report.adapter_mismatches.extend(mismatches)
            except Exception as exc:
                report.issues.append(f"Adapter mismatch check failed: {exc}")

        return report

    # ----- helpers -----

    def _load_yaml(self, path: Path) -> Any:
        import yaml
        raw = path.read_text(encoding="utf-8")
        return yaml.safe_load(raw) or {}

    def _has_valid_outputs(self, outputs: Any, wmb: Path) -> bool:
        if not outputs:
            return False
        if isinstance(outputs, dict):
            output_files = list(outputs.values())
        elif isinstance(outputs, list):
            output_files = outputs
        else:
            return False
        for op in output_files:
            if isinstance(op, str) and not (wmb.parent / op).exists():
                return False
        return bool(output_files)

    def _outputs_changed(self, task_id: str, outputs: Any, wmb: Path) -> bool:
        lock_path = wmb / "artifacts" / f"{task_id}_output_hash.json"
        if not lock_path.exists():
            return False  # no previous hash to compare
        try:
            previous = json.loads(lock_path.read_text(encoding="utf-8"))
        except Exception:
            return False
        # Compute current hash
        if isinstance(outputs, dict):
            output_files = list(outputs.values())
        elif isinstance(outputs, list):
            output_files = outputs
        else:
            output_files = []
        current = {}
        for op in output_files:
            if isinstance(op, str):
                p = wmb.parent / op
                if p.exists():
                    current[op] = str(p.stat().st_mtime)
        return previous != current

    def _check_adapter_mismatch(self, adapter_state: Any, wmb: Path) -> list[str]:
        mismatches: list[str] = []
        adapter_file = wmb / "adapter_state.yaml"
        if not adapter_file.exists():
            return mismatches
        try:
            saved = self._load_yaml(adapter_file)
        except Exception:
            return mismatches
        if isinstance(adapter_state, dict) and isinstance(saved, dict):
            for key in set(adapter_state) | set(saved):
                if adapter_state.get(key) != saved.get(key):
                    mismatches.append(f"Adapter mismatch: {key!r}")
        return mismatches
