"""Persistent WMB project initialization."""

from __future__ import annotations

import os
import time
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
_PUBLISH_LOCK_ATTEMPTS = 1_000
_PUBLISH_LOCK_DELAY_SECONDS = 0.001


def _publish_lock_path(path: Path) -> Path:
    return path.with_name(f".{path.name}.publish.lock")


def _wait_for_publish(path: Path) -> None:
    lock_path = _publish_lock_path(path)
    for _ in range(_PUBLISH_LOCK_ATTEMPTS):
        if not os.path.lexists(lock_path):
            return
        time.sleep(_PUBLISH_LOCK_DELAY_SECONDS)
    raise TimeoutError(f"timed out waiting for project record: {path}")


def _atomic_publish_once(temporary_path: Path, path: Path) -> None:
    """Atomically publish a complete temporary file without clobbering."""

    lock_path = _publish_lock_path(path)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_BINARY"):
        flags |= os.O_BINARY

    descriptor: int | None = None
    for _ in range(_PUBLISH_LOCK_ATTEMPTS):
        try:
            descriptor = os.open(lock_path, flags, 0o600)
            break
        except (FileExistsError, PermissionError):
            if os.path.lexists(path):
                return
            time.sleep(_PUBLISH_LOCK_DELAY_SECONDS)
    if descriptor is None:
        raise TimeoutError(f"timed out publishing project record: {path}")

    try:
        if not os.path.lexists(path):
            os.rename(temporary_path, path)
    finally:
        os.close(descriptor)
        lock_path.unlink(missing_ok=True)


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
        try:
            link = getattr(os, "link", None)
            if link is None:
                raise NotImplementedError
            link(temporary_path, path)
        except FileExistsError:
            pass
        except (OSError, NotImplementedError):
            _atomic_publish_once(temporary_path, path)
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


def _placeholder_author_queue() -> dict[str, Any]:
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


def _author_queue(author: Mapping[str, Any] | str | None) -> dict[str, Any]:
    if author is None:
        return _placeholder_author_queue()
    if isinstance(author, str):
        display_name = author.strip()
        if not display_name:
            return _placeholder_author_queue()
        author = {"display_name": display_name, "status": "confirmed"}
    else:
        author = dict(author)
        display_name = author.get("display_name")
        if not isinstance(display_name, str) or not display_name.strip():
            return _placeholder_author_queue()
        author["display_name"] = display_name.strip()
        status = author.get("status")
        if not isinstance(status, str) or not status.strip():
            raise ValueError("author status is required")
        author["status"] = status.strip()

    if author["status"] == "confirmed":
        return {"author": author, "items": []}
    if author["status"] == "placeholder":
        return {
            "author": author,
            "items": [
                {
                    "field": "author_identity",
                    "placeholder": author["display_name"],
                    "status": "pending",
                }
            ],
        }
    raise ValueError("author status must be 'confirmed' or 'placeholder'")


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


def _validate_existing_run(path: Path) -> bool:
    _wait_for_publish(path)
    if not os.path.lexists(path):
        return False
    if not path.is_file():
        raise IsADirectoryError(f"run state is not a file: {path}")

    run = yaml.safe_load(path.read_text(encoding="utf-8"))
    validate_contract("run", run)
    return True


def initialize_project(
    root: str | Path,
    author: Mapping[str, Any] | str | None = None,
    journal: Mapping[str, Any] | str | None = None,
) -> ProjectPaths:
    """Create persistent WMB state at ``root`` without replacing records."""

    project = ProjectPaths(Path(root))
    run_exists = _validate_existing_run(project.run_file)
    author_queue = _author_queue(author)
    journal_contract = _journal_contract(journal)

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

    if not run_exists:
        _write_yaml_once(project.run_file, run)
    _validate_existing_run(project.run_file)
    _write_yaml_once(
        project.author_confirmation_queue_file,
        author_queue,
    )
    _write_yaml_once(project.journal_contract_file, journal_contract)
    _write_once(project.events_log, "")
    _write_once(project.rejections_log, "")
    return project
