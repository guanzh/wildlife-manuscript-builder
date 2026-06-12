"""Shared data models for persistent WMB projects."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProjectPaths:
    """Canonical filesystem locations for one WMB project."""

    root: Path

    def __post_init__(self) -> None:
        object.__setattr__(self, "root", Path(self.root))

    @property
    def wmb_dir(self) -> Path:
        return self.root / ".wmb"

    @property
    def tasks_dir(self) -> Path:
        return self.wmb_dir / "tasks"

    @property
    def artifacts_dir(self) -> Path:
        return self.wmb_dir / "artifacts"

    @property
    def reviews_dir(self) -> Path:
        return self.wmb_dir / "reviews"

    @property
    def decisions_dir(self) -> Path:
        return self.wmb_dir / "decisions"

    @property
    def logs_dir(self) -> Path:
        return self.wmb_dir / "logs"

    @property
    def run_file(self) -> Path:
        return self.wmb_dir / "run.yaml"

    @property
    def author_confirmation_queue_file(self) -> Path:
        return self.wmb_dir / "author_confirmation_queue.yaml"

    @property
    def journal_contract_file(self) -> Path:
        return self.wmb_dir / "journal_contract.yaml"

    @property
    def events_log(self) -> Path:
        return self.logs_dir / "events.jsonl"

    @property
    def rejections_log(self) -> Path:
        return self.logs_dir / "rejections.jsonl"
