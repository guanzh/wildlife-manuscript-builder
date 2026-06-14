"""Author-confirmation gate for scientific workflow changes."""

from __future__ import annotations

import enum
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from uuid import uuid4


# ---------- change categories ----------

MAJOR_CATEGORIES = frozenset({
    "research_question",
    "core_hypothesis",
    "response_variable",
    "core_model",
    "inferential_target",
    "key_sample_exclusion",
    "key_inclusion_criteria",
    "unsupported_research_direction",
    "final_submission_package",
    "authorship_or_declarations",
})

LOW_RISK_CATEGORIES = frozenset({
    "claim_narrowing",
    "citation_sync",
    "figure_table_sync",
    "method_description",
    "language_structure",
    "format_repair",
})

QUEUE_RELPATH = "author_confirmation_queue.yaml"


class GateDecision(str, enum.Enum):
    AWAITING_AUTHOR_CONFIRMATION = "awaiting_author_confirmation"
    AUTO_REFINE = "auto_refine"
    BLOCKED_UNKNOWN_CHANGE = "blocked_unknown_change"


@dataclass(frozen=True)
class ChangeDecision:
    """Immutable outcome of a Gate evaluation."""
    status: GateDecision
    change_type: str
    summary: str
    queue_item_id: str | None = None
    reason: str | None = None


@dataclass
class QueuedItem:
    """A single pending author-confirmation item."""
    item_id: str
    change_type: str
    summary: str
    project_state_snapshot: dict[str, Any] | None = None


# ---------- Gate engine ----------

class GateEngine:
    """Evaluate whether a proposed change requires author confirmation."""

    def __init__(self, project: Any) -> None:
        self._project = project
        self._queue_path_cached: Path | None = None

    def evaluate_change(self, change: dict[str, Any]) -> ChangeDecision:
        """Evaluate a single change and return an immutable decision."""
        change_type = change.get("change_type", "")
        summary = change.get("summary", "")

        if not change_type:
            return ChangeDecision(
                status=GateDecision.BLOCKED_UNKNOWN_CHANGE,
                change_type="",
                summary="Empty or missing change_type",
                reason="change_type is required",
            )

        if change_type in LOW_RISK_CATEGORIES:
            return ChangeDecision(
                status=GateDecision.AUTO_REFINE,
                change_type=change_type,
                summary=summary,
            )

        if change_type in MAJOR_CATEGORIES:
            item_id = self._enqueue_author_confirmation(change)
            return ChangeDecision(
                status=GateDecision.AWAITING_AUTHOR_CONFIRMATION,
                change_type=change_type,
                summary=summary,
                queue_item_id=item_id,
                reason="Author confirmation required for major change",
            )

        return ChangeDecision(
            status=GateDecision.BLOCKED_UNKNOWN_CHANGE,
            change_type=change_type,
            summary=summary,
            reason=f"Unknown change category: {change_type!r}",
        )

    # ---- queue management ----

    def _queue_path(self) -> Path:
        if self._queue_path_cached is None:
            self._queue_path_cached = self._resolve_queue_path()
        return self._queue_path_cached

    def _resolve_queue_path(self) -> Path:
        base = getattr(self._project, "paths", None)
        if base is None:
            return Path.cwd() / ".wmb" / QUEUE_RELPATH
        return base.wmb_dir / QUEUE_RELPATH

    def _enqueue_author_confirmation(self, change: dict[str, Any]) -> str:
        """Append one idempotent pending item. Repeated identical changes
        produce no duplicate queue entry."""
        path = self._queue_path()
        path.parent.mkdir(parents=True, exist_ok=True)

        # check duplicates
        existing = self._pending_items()
        for item in existing:
            if (
                item.get("change_type") == change.get("change_type")
                and item.get("summary") == change.get("summary")
            ):
                return item.get("item_id", "")

        item_id = f"acq_{uuid4().hex[:12]}"
        entry = {
            "item_id": item_id,
            "change_type": change.get("change_type", ""),
            "summary": change.get("summary", ""),
        }
        existing.append(entry)
        self._write_queue(existing)
        return item_id

    def _pending_items(self) -> list[dict[str, Any]]:
        path = self._queue_path()
        if not path.exists():
            return []
        import yaml
        try:
            with open(str(path), "r", encoding="utf-8") as fh:
                data = yaml.safe_load(fh)
            return data if isinstance(data, list) else []
        except Exception:
            return []

    def _write_queue(self, items: list[dict[str, Any]]) -> None:
        import yaml
        path = self._queue_path()
        with open(str(path), "w", encoding="utf-8", newline="\n") as fh:
            yaml.safe_dump(items, fh, default_flow_style=False, sort_keys=False)

    def pending_confirmations(self) -> list[QueuedItem]:
        items = self._pending_items()
        return [
            QueuedItem(
                item_id=i.get("item_id", ""),
                change_type=i.get("change_type", ""),
                summary=i.get("summary", ""),
            )
            for i in items
        ]

    def clear_confirmation(self, item_id: str) -> bool:
        items = self._pending_items()
        new_items = [i for i in items if i.get("item_id") != item_id]
        if len(new_items) == len(items):
            return False
        self._write_queue(new_items)
        return True
