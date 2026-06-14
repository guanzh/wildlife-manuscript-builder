"""Author-confirmation gate for scientific workflow changes."""

from __future__ import annotations

import enum
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any
from uuid import uuid4


MAJOR_CATEGORIES = frozenset({
    "research_question", "core_hypothesis", "response_variable",
    "core_model", "inferential_target", "key_sample_exclusion",
    "key_inclusion_criteria", "unsupported_research_direction",
    "final_submission_package", "authorship_or_declarations",
})

LOW_RISK_CATEGORIES = frozenset({
    "claim_narrowing", "citation_sync", "figure_table_sync",
    "method_description", "language_structure", "format_repair",
})


class GateDecision(str, enum.Enum):
    AWAITING_AUTHOR_CONFIRMATION = "awaiting_author_confirmation"
    AUTO_REFINE = "auto_refine"
    BLOCKED_UNKNOWN_CHANGE = "blocked_unknown_change"


@dataclass(frozen=True)
class ChangeDecision:
    status: GateDecision
    change_type: str
    summary: str
    queue_item_id: str | None = None
    reason: str | None = None


class GateEngine:
    """Evaluate whether a proposed change requires author confirmation.
    Queue file structure (YAML):
        author: str (Dr. Who default)
        items:
          - item_id: ...
            change_type: ...
            summary: ...
    Atomic writes via NamedTemporaryFile + rename.
    """

    def __init__(self, project: Any) -> None:
        self._project = project
        self._queue_path_cached: Path | None = None

    def evaluate_change(self, change: dict[str, Any]) -> ChangeDecision:
        change_type = change.get("change_type", "")
        summary = change.get("summary", "")

        if not change_type:
            return ChangeDecision(
                status=GateDecision.BLOCKED_UNKNOWN_CHANGE,
                change_type="", summary="Empty or missing change_type",
                reason="change_type is required",
            )

        if change_type in LOW_RISK_CATEGORIES:
            return ChangeDecision(
                status=GateDecision.AUTO_REFINE,
                change_type=change_type, summary=summary,
            )

        if change_type in MAJOR_CATEGORIES:
            item_id = self._enqueue(change)
            return ChangeDecision(
                status=GateDecision.AWAITING_AUTHOR_CONFIRMATION,
                change_type=change_type, summary=summary,
                queue_item_id=item_id,
                reason="Author confirmation required for major change",
            )

        return ChangeDecision(
            status=GateDecision.BLOCKED_UNKNOWN_CHANGE,
            change_type=change_type, summary=summary,
            reason=f"Unknown change category: {change_type!r}",
        )

    def _queue_path(self) -> Path:
        if self._queue_path_cached is None:
            base = getattr(self._project, "paths", None)
            if base is not None:
                self._queue_path_cached = Path(str(base.wmb_dir)) / "author_confirmation_queue.yaml"
            else:
                self._queue_path_cached = Path.cwd() / ".wmb" / "author_confirmation_queue.yaml"
        return self._queue_path_cached

    def _read_queue(self) -> dict[str, Any]:
        """Return {'author': ..., 'items': [...]}."""
        path = self._queue_path()
        if not path.exists():
            return {"author": "Dr. Who", "items": []}
        try:
            import yaml
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
            if isinstance(data, dict) and "author" in data:
                return data
            # If it's a bare list (old format), wrap it
            if isinstance(data, list):
                return {"author": "Dr. Who", "items": data}
            return {"author": "Dr. Who", "items": []}
        except Exception:
            return {"author": "Dr. Who", "items": []}

    def _write_queue_atomic(self, data: dict[str, Any]) -> None:
        """Atomic YAML write using tempfile + rename."""
        import yaml
        path = self._queue_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = NamedTemporaryFile(
            mode="w", encoding="utf-8", suffix=".yaml", delete=False,
            dir=str(path.parent),
        )
        try:
            yaml.safe_dump(data, tmp, default_flow_style=False, sort_keys=False, allow_unicode=True)
            tmp.close()
            os.replace(tmp.name, str(path))
        except Exception:
            try:
                os.unlink(tmp.name)
            except Exception:
                pass
            raise

    def _enqueue(self, change: dict[str, Any]) -> str:
        """Append one idempotent pending item. Does not overwrite author."""
        queue = self._read_queue()
        # Ensure author field is preserved
        if "author" not in queue:
            queue["author"] = "Dr. Who"
        if "items" not in queue:
            queue["items"] = []

        # Deduplicate: identical change_type + summary
        for item in queue["items"]:
            if (
                item.get("change_type") == change.get("change_type")
                and item.get("summary") == change.get("summary")
            ):
                return item.get("item_id", "")

        item_id = f"acq_{uuid4().hex[:12]}"
        queue["items"].append({
            "item_id": item_id,
            "change_type": change.get("change_type", ""),
            "summary": change.get("summary", ""),
        })
        self._write_queue_atomic(queue)
        return item_id

    def pending_confirmations(self) -> list[dict[str, Any]]:
        queue = self._read_queue()
        return queue.get("items", [])

    def clear_confirmation(self, item_id: str) -> bool:
        queue = self._read_queue()
        items = queue.get("items", [])
        new_items = [i for i in items if i.get("item_id") != item_id]
        if len(new_items) == len(items):
            return False
        queue["items"] = new_items
        self._write_queue_atomic(queue)
        return True
