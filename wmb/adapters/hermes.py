"""Hermes-specific task adapter (Durable Kanban)."""

from __future__ import annotations

import json
import shlex
import subprocess
from typing import Any

from wmb.adapters.base import BaseAdapter, DispatchPacket, IngestResult

_CAPABILITY_PROFILE: dict[str, str] = {
    "manuscript_writer": "default",
    "reviewer": "default",
    "data_analyst": "default",
    "literature_searcher": "default",
}


class HermesAdapter(BaseAdapter):
    """Adapter that builds Hermes Durable Kanban commands.

    Uses hermes kanban create syntax. Command construction uses an
    argument list, never a shell string. Tests inject a fake runner.
    """

    def __init__(self, runner: Any | None = None) -> None:
        self._runner = runner or subprocess.run
        self._last_command: list[str] | None = None
        self._last_result: dict[str, Any] | None = None

    @property
    def adapter_name(self) -> str:
        return "hermes"

    def prepare_dispatch(
        self, task: dict[str, Any], dependencies: list[str] | None = None
    ) -> DispatchPacket:
        """Build a structured packet; the actual Kanban command is built
        by build_create_command."""
        capability = task.get("capability", "")
        isolated = "reviewer" in capability.lower()

        return DispatchPacket(
            adapter="hermes",
            task_contract=task,
            result_contract={},
            objective=task.get("objective", ""),
            capability=capability,
            allowed_inputs=task.get("allowed_inputs"),
            required_outputs=task.get("required_outputs"),
            isolated_context=isolated,
        )

    def build_create_command(
        self, task: dict[str, Any], dependencies: list[str] | None = None
    ) -> list[str]:
        """Build a 'hermes kanban create' argument list.

        Never returns a shell string (security). Each call returns a
        fresh list. Dependencies become repeated --parent arguments.
        """
        task_id = task.get("task_id", "unknown")
        title = task.get("title", task.get("objective", f"WMB task {task_id}"))
        capability = task.get("capability", "unknown")
        profile = _CAPABILITY_PROFILE.get(capability, "default")
        workspace = f"dir:{task.get('workspace', '.')}"
        max_runtime = task.get("max_runtime", "2h")
        max_retries = str(task.get("max_retries", 2))

        cmd = [
            "hermes", "kanban", "create",
            title,
            "--body", self._build_body(task),
            "--assignee", profile,
            "--workspace", workspace,
            "--idempotency-key", f"wmb-{task_id}",
            "--max-runtime", max_runtime,
            "--max-retries", max_retries,
        ]

        if task.get("goal_mode"):
            cmd.append("--goal")

        if dependencies:
            for dep in dependencies:
                cmd.extend(["--parent", dep])

        self._last_command = cmd
        return cmd

    def execute_dispatch(
        self,
        task: dict[str, Any],
        dependencies: list[str] | None = None,
        runner: Any | None = None,
    ) -> IngestResult:
        """Build and execute the dispatch command."""
        r = runner or self._runner
        cmd = self.build_create_command(task, dependencies)
        try:
            result = r(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                return IngestResult(accepted=True, task_updated=True)
            return IngestResult(
                accepted=False,
                task_updated=False,
                errors=[result.stderr or f"exit {result.returncode}"],
            )
        except Exception as exc:
            return IngestResult(
                accepted=False, task_updated=False, errors=[str(exc)],
            )

    def _build_body(self, task: dict[str, Any]) -> str:
        """Build the task body with canonical paths and instructions."""
        parts = [
            f"Task: {task.get('objective', '')}",
            f"Capability: {task.get('capability', '')}",
        ]
        if task.get("task_contract_path"):
            parts.append(f"Contract: {task['task_contract_path']}")
        if task.get("result_contract_path"):
            parts.append(f"Results: {task['result_contract_path']}")
        parts.append("")
        parts.append("Instructions:")
        parts.append("- Write structured result to the contract path")
        parts.append("- Do not change .wmb/run.yaml")
        parts.append("- Stop on prohibited action")
        return "\n".join(parts)

    def ingest_result(self, result: dict[str, Any]) -> IngestResult:
        """Validate and store a Hermes result."""
        if not isinstance(result, dict):
            return IngestResult(accepted=False, task_updated=False, errors=["Result must be a dict"])
        if "task_id" not in result:
            return IngestResult(accepted=False, task_updated=False, errors=["Missing task_id"])
        self._last_result = result
        return IngestResult(accepted=True, task_updated=True)

    def reconcile(self) -> IngestResult | None:
        return None

    def last_command(self) -> list[str] | None:
        return self._last_command
