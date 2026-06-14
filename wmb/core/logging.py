"""Rejection ledger for workflow decision logging."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from uuid import uuid4

VALID_ACTIONS = frozenset({
    "failed",
    "skipped",
    "excluded",
    "retried",
    "dropped_claim",
    "rejected_source",
})

REJECTIONS_RELPATH = "logs/rejections.jsonl"


class RejectionLedger:
    """Append-only JSONL ledger for blocked, excluded, and rejected items."""

    def __init__(self, project: Any) -> None:
        self._log_path: Path | None = None
        self._project = project

    def _resolve_path(self) -> Path:
        base = getattr(self._project, "paths", None)
        if base is None:
            return Path.cwd() / ".wmb" / REJECTIONS_RELPATH
        return base.wmb_dir / REJECTIONS_RELPATH

    @property
    def log_path(self) -> Path:
        if self._log_path is None:
            self._log_path = self._resolve_path()
        return self._log_path

    def record(
        self,
        action: str,
        summary: str,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Append one JSONL entry. Returns the entry ID.

        Parameters
        ----------
        action:
            One of: failed, skipped, excluded, retried, dropped_claim,
            rejected_source.
        summary:
            Human-readable description of the rejection. Must be non-empty.
        metadata:
            Optional additional structured data.

        Returns
        -------
        str:
            The unique entry ID.

        Raises
        ------
        ValueError:
            If action is not in VALID_ACTIONS or summary is empty.
        """
        if action not in VALID_ACTIONS:
            raise ValueError(
                f"Invalid rejection action: {action!r}. "
                f"Must be one of {sorted(VALID_ACTIONS)}"
            )
        if not summary or not summary.strip():
            raise ValueError("Rejection summary must be non-empty")

        entry_id = f"rj_{uuid4().hex[:12]}"
        entry = {
            "entry_id": entry_id,
            "action": action,
            "summary": summary.strip(),
            "metadata": metadata or {},
        }

        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(str(self.log_path), "a", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n")

        return entry_id

    def entries(self) -> list[dict[str, Any]]:
        """Return all ledger entries."""
        if not self.log_path.exists():
            return []
        result: list[dict[str, Any]] = []
        with open(str(self.log_path), "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    try:
                        result.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
        return result
