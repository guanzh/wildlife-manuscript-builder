"""Persistent WMB project initialization."""

from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any
from uuid import uuid4

import yaml

from wmb.contracts import validate_contract
from wmb.core.models import ProjectPaths

DEFAULT_JOURNAL_URL = (
    "https://www.biodiversity-science.net/CN/column/column49.shtml"
)


def _write_once(path: Path, content: str) -> None:
    """Atomically create a record without replacing an existing one."""

    if path.exists():
        return

    temporary_path: Path | None = None
    try:
        with NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary.write(content)
            temporary.flush()
            os.fsync(temporary.fileno())
            temporary_path = Path(temporary.name)
        os.link(temporary_path, path)
    except FileExistsError:
        pass
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def _write_yaml_once(path: Path, payload: Mapping[str, Any]) -> None:
    content = yaml.safe_dump(
        dict(payload),
        allow_unicode=True,
        sort_keys=False,
    )
    _write_once(path, content)


def _author_queue(author: Mapping[str, Any] | str | None) -> dict[str, Any]:
    if author is None:
        return {
            "author": {"display_name": "Dr. Who", "status": "placeholder"},
            "items": [
                {
                    "field": "author_identity",
                    "placeholder": "Dr. Who",
                    "status": "pending",
                }
            ],
        }
    if isinstance(author, str):
        author = {"display_name": author, "status": "confirmed"}
    return {"author": dict(author), "items": []}


def _journal_contract(journal: Mapping[str, Any] | str | None) -> dict[str, Any]:
    if journal is None:
        return {
            "journal_name": "生物多样性",
            "main_language": "zh-CN",
            "bilingual_elements": ["title", "abstract", "keywords"],
            "source_url": DEFAULT_JOURNAL_URL,
        }
    if isinstance(journal, str):
        return {"journal_name": journal}
    return dict(journal)


def initialize_project(
    root: str | Path,
    author: Mapping[str, Any] | str | None = None,
    journal: Mapping[str, Any] | str | None = None,
) -> ProjectPaths:
    """Create persistent WMB state at ``root`` without replacing records."""

    project = ProjectPaths(Path(root))
    for directory in (
        project.tasks_dir,
        project.artifacts_dir,
        project.reviews_dir,
        project.decisions_dir,
        project.logs_dir,
    ):
        directory.mkdir(parents=True, exist_ok=True)

    run = {
        "run_id": f"run-{uuid4().hex}",
        "status": "intake",
        "current_gate": "data_contract",
        "delivery_level": 0,
    }
    validate_contract("run", run)

    _write_yaml_once(project.run_file, run)
    _write_yaml_once(
        project.author_confirmation_queue_file,
        _author_queue(author),
    )
    _write_yaml_once(project.journal_contract_file, _journal_contract(journal))
    _write_once(project.events_log, "")
    _write_once(project.rejections_log, "")
    return project
