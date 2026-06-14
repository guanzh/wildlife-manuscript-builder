"""Shared adapter protocol for execution-platform dispatch."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class DispatchPacket:
    """Platform-agnostic structured task packet returned by prepare_dispatch."""
    adapter: str
    task_contract: dict[str, Any]
    result_contract: dict[str, Any]
    objective: str
    capability: str
    allowed_inputs: list[str] | None = None
    required_outputs: list[str] | None = None
    isolated_context: bool = False


@dataclass
class IngestResult:
    """Result from ingesting a platform result."""
    accepted: bool
    task_updated: bool
    errors: list[str] | None = None


class BaseAdapter(ABC):
    """Abstract base for Codex/Hermes adapters.

    Adapters prepare dispatch, ingest results, and reconcile task execution
    status. They must NOT call StateStore.transition() or decide a Gate.
    """

    @property
    @abstractmethod
    def adapter_name(self) -> str:
        ...

    @abstractmethod
    def prepare_dispatch(
        self, task: dict[str, Any], dependencies: list[str] | None = None
    ) -> DispatchPacket:
        """Build a structured packet for dispatching the task."""
        ...

    @abstractmethod
    def ingest_result(self, result: dict[str, Any]) -> IngestResult:
        """Validate and process a structured result from a task.

        May update task execution status but must NOT change canonical
        Gate/run state.
        """
        ...

    @abstractmethod
    def reconcile(self) -> IngestResult | None:
        """Reconcile outstanding task state. Idempotent."""
        ...
