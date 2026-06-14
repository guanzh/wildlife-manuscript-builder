"""Codex-specific task adapter."""

from __future__ import annotations

from typing import Any

from wmb.adapters.base import BaseAdapter, DispatchPacket, IngestResult


class CodexAdapter(BaseAdapter):
    """Adapter that produces structured Codex task packets.

    prepare_dispatch returns a packet with isolated-reviewer awareness.
    It does not invoke Codex tools from Python.
    """

    def __init__(self) -> None:
        self._last_result: dict[str, Any] | None = None

    @property
    def adapter_name(self) -> str:
        return "codex"

    def prepare_dispatch(
        self, task: dict[str, Any], dependencies: list[str] | None = None
    ) -> DispatchPacket:
        """Build a Codex dispatch packet."""
        capability = task.get("capability", "")
        isolated = "reviewer" in capability.lower()

        return DispatchPacket(
            adapter="codex",
            task_contract=task,
            result_contract={},
            objective=task.get("objective", ""),
            capability=capability,
            allowed_inputs=task.get("allowed_inputs"),
            required_outputs=task.get("required_outputs"),
            isolated_context=isolated,
        )

    def ingest_result(self, result: dict[str, Any]) -> IngestResult:
        """Validate and store a Codex result."""
        if not isinstance(result, dict):
            return IngestResult(accepted=False, task_updated=False, errors=["Result must be a dict"])
        if "task_id" not in result:
            return IngestResult(accepted=False, task_updated=False, errors=["Missing task_id"])
        self._last_result = result
        return IngestResult(accepted=True, task_updated=True)

    def reconcile(self) -> IngestResult | None:
        return None

    def last_result(self) -> dict[str, Any] | None:
        return self._last_result
