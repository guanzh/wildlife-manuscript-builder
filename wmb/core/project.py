"""Persistent WMB project initialization."""

from __future__ import annotations

import json
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
_PUBLISH_LOCK_STALE_SECONDS = 30.0
_FINAL_VALIDATION_ATTEMPTS = 3


class InitializationError(RuntimeError):
    """Raised when initialization cannot produce a complete valid project."""


def _publish_lock_path(path: Path) -> Path:
    return path.with_name(f".{path.name}.publish.lock")


def _exclusive_flags() -> int:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_BINARY"):
        flags |= os.O_BINARY
    return flags


def _write_descriptor(descriptor: int, content: str) -> None:
    data = content.encode("utf-8")
    written = 0
    try:
        while written < len(data):
            count = os.write(descriptor, data[written:])
            if count == 0:
                raise OSError("zero-byte write while publishing project record")
            written += count
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _lock_bytes(lock_path: Path) -> bytes | None:
    try:
        return lock_path.read_bytes()
    except (FileNotFoundError, PermissionError):
        return None


def _remove_lock_if_unchanged(lock_path: Path, expected: bytes | None) -> bool:
    if expected is None or _lock_bytes(lock_path) != expected:
        return False
    try:
        lock_path.unlink()
    except (FileNotFoundError, PermissionError):
        return False
    return True


def _unlink_if_same_file(path: Path, identity: tuple[int, int]) -> None:
    try:
        current = path.stat(follow_symlinks=False)
    except (FileNotFoundError, PermissionError):
        return
    if (current.st_dev, current.st_ino) == identity:
        path.unlink(missing_ok=True)


def _lock_is_stale(lock_path: Path) -> bool:
    try:
        age = time.time() - lock_path.stat().st_mtime
    except (FileNotFoundError, PermissionError):
        return False
    return age >= _PUBLISH_LOCK_STALE_SECONDS


def _path_is_valid(path: Path, validator) -> bool:
    if not path.is_file():
        return False
    try:
        validator(path)
    except Exception:
        return False
    return True


def _wait_for_publish(path: Path, validator=None) -> None:
    lock_path = _publish_lock_path(path)
    for _ in range(_PUBLISH_LOCK_ATTEMPTS):
        if not os.path.lexists(lock_path):
            return
        lock_data = _lock_bytes(lock_path)
        if validator is not None and _path_is_valid(path, validator):
            _remove_lock_if_unchanged(lock_path, lock_data)
            return
        if _lock_is_stale(lock_path):
            _remove_lock_if_unchanged(lock_path, lock_data)
            continue
        time.sleep(_PUBLISH_LOCK_DELAY_SECONDS)
    raise TimeoutError(f"timed out waiting for project record: {path}")


def _acquire_publish_lock(path: Path) -> tuple[Path, bytes] | None:
    lock_path = _publish_lock_path(path)
    lock_data = json.dumps(
        {
            "pid": os.getpid(),
            "created_at": time.time(),
            "token": uuid4().hex,
        },
        sort_keys=True,
    ).encode("utf-8")

    for _ in range(_PUBLISH_LOCK_ATTEMPTS):
        try:
            descriptor = os.open(lock_path, _exclusive_flags(), 0o600)
        except (FileExistsError, PermissionError):
            _wait_for_publish(path)
            if os.path.lexists(path):
                return None
            continue
        try:
            _write_descriptor(descriptor, lock_data.decode("utf-8"))
        except Exception:
            _remove_lock_if_unchanged(lock_path, _lock_bytes(lock_path))
            raise
        return lock_path, lock_data
    raise TimeoutError(f"timed out publishing project record: {path}")


def _exclusive_publish_once(path: Path, content: str) -> None:
    """Publish via exclusive target creation without replacing competitors."""

    lock = _acquire_publish_lock(path)
    if lock is None:
        return
    lock_path, lock_data = lock
    try:
        try:
            descriptor = os.open(path, _exclusive_flags(), 0o666)
        except (FileExistsError, PermissionError):
            if os.path.lexists(path):
                return
            raise
        created = os.fstat(descriptor)
        identity = (created.st_dev, created.st_ino)
        try:
            _write_descriptor(descriptor, content)
        except Exception:
            _unlink_if_same_file(path, identity)
            raise
    finally:
        _remove_lock_if_unchanged(lock_path, lock_data)


def _write_once(path: Path, content: str) -> None:
    """Atomically create a record without replacing an existing one."""

    if os.path.lexists(path):
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
            _exclusive_publish_once(path, content)
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


def _default_journal_contract() -> dict[str, Any]:
    return {
        "journal_name": "生物多样性",
        "main_language": "zh-CN",
        "bilingual_elements": ["title", "abstract", "keywords"],
        "source_url": DEFAULT_JOURNAL_URL,
    }


def _nonblank_string(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-blank string")
    return value.strip()


def _validate_journal_contract(payload: object) -> None:
    if not isinstance(payload, Mapping):
        raise ValueError("journal contract must be a mapping")
    _nonblank_string(payload.get("journal_name"), "journal_name")
    _nonblank_string(payload.get("main_language"), "main_language")
    _nonblank_string(payload.get("source_url"), "source_url")
    bilingual = payload.get("bilingual_elements")
    if not isinstance(bilingual, list) or any(
        not isinstance(item, str) or not item.strip() for item in bilingual
    ):
        raise ValueError("journal bilingual_elements must be a string list")


def _journal_contract(journal: Mapping[str, Any] | str | None) -> dict[str, Any]:
    if journal is None:
        return _default_journal_contract()
    if isinstance(journal, str):
        if not journal.strip():
            return _default_journal_contract()
        raise ValueError("journal must be supplied as a complete contract mapping")
    contract = dict(journal)
    if not contract or all(
        value is None
        or value == ""
        or isinstance(value, str)
        and not value.strip()
        or value == []
        or value == {}
        for value in contract.values()
    ):
        return _default_journal_contract()
    try:
        _validate_journal_contract(contract)
    except ValueError as exc:
        raise ValueError(f"invalid journal contract: {exc}") from exc
    contract["journal_name"] = contract["journal_name"].strip()
    contract["main_language"] = contract["main_language"].strip()
    contract["source_url"] = contract["source_url"].strip()
    return contract


def _validate_author_queue(payload: object) -> None:
    if not isinstance(payload, Mapping):
        raise ValueError("author confirmation queue must be a mapping")
    author = payload.get("author")
    items = payload.get("items")
    if not isinstance(author, Mapping) or not isinstance(items, list):
        raise ValueError("author confirmation queue requires author and items")
    _nonblank_string(author.get("display_name"), "author display_name")
    status = _nonblank_string(author.get("status"), "author status")
    if status not in {"confirmed", "placeholder"}:
        raise ValueError("author status must be 'confirmed' or 'placeholder'")
    for item in items:
        if not isinstance(item, Mapping):
            raise ValueError("author confirmation items must be mappings")
        _nonblank_string(item.get("field"), "author confirmation field")
        _nonblank_string(item.get("status"), "author confirmation status")
    if status == "placeholder" and not any(
        item.get("field") == "author_identity" and item.get("status") == "pending"
        for item in items
    ):
        raise ValueError("placeholder author requires pending author_identity")


def _validate_run_file(path: Path) -> None:
    validate_contract("run", yaml.safe_load(path.read_text(encoding="utf-8")))


def _validate_author_file(path: Path) -> None:
    _validate_author_queue(yaml.safe_load(path.read_text(encoding="utf-8")))


def _validate_journal_file(path: Path) -> None:
    _validate_journal_contract(yaml.safe_load(path.read_text(encoding="utf-8")))


def _validate_jsonl_file(path: Path, contract_kind: str | None = None) -> None:
    for line_number, line in enumerate(
        path.read_text(encoding="utf-8").splitlines(),
        start=1,
    ):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSONL record at line {line_number}") from exc
        if not isinstance(record, Mapping) or not record:
            raise ValueError(f"JSONL line {line_number} must be a non-empty object")
        if contract_kind is not None:
            validate_contract(contract_kind, record)


def _validate_existing_record(path: Path, validator) -> bool:
    _wait_for_publish(path, validator)
    if not os.path.lexists(path):
        return False
    if not path.is_file():
        raise IsADirectoryError(f"project record is not a file: {path}")
    validator(path)
    return True


def _validate_existing_run(path: Path) -> bool:
    return _validate_existing_record(path, _validate_run_file)


def _ensure_directory(path: Path) -> None:
    if os.path.lexists(path) and not path.is_dir():
        raise NotADirectoryError(f"project directory is not a directory: {path}")
    path.mkdir(parents=True, exist_ok=True)


def _project_records(project: ProjectPaths):
    return (
        (project.run_file, _validate_run_file),
        (project.author_confirmation_queue_file, _validate_author_file),
        (project.journal_contract_file, _validate_journal_file),
        (
            project.events_log,
            lambda path: _validate_jsonl_file(path, "event"),
        ),
        (project.rejections_log, _validate_jsonl_file),
    )


def _record_signature(path: Path) -> tuple[int, int, int, int] | None:
    try:
        stat = path.stat(follow_symlinks=False)
    except (FileNotFoundError, PermissionError):
        return None
    return (stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns)


def _require_complete_project(project: ProjectPaths) -> None:
    records = _project_records(project)
    for attempt in range(_FINAL_VALIDATION_ATTEMPTS):
        before = {path: _record_signature(path) for path, _ in records}
        for path, validator in records:
            try:
                exists = _validate_existing_record(path, validator)
            except Exception as exc:
                raise InitializationError(
                    f"initialized project record is invalid: {path}: {exc}"
                ) from exc
            if exists:
                continue
            raise InitializationError(
                f"initialized project record is missing: {path}"
            )
        after = {path: _record_signature(path) for path, _ in records}
        if before == after and all(signature is not None for signature in after.values()):
            return
        if attempt + 1 < _FINAL_VALIDATION_ATTEMPTS:
            time.sleep(_PUBLISH_LOCK_DELAY_SECONDS)

    changed = ", ".join(
        str(path)
        for path in before
        if before[path] != after[path] or after[path] is None
    )
    raise InitializationError(
        f"initialized project state did not stabilize: {changed}"
    )


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
    _validate_author_queue(author_queue)
    _validate_journal_contract(journal_contract)

    _validate_existing_record(
        project.author_confirmation_queue_file,
        _validate_author_file,
    )
    _validate_existing_record(project.journal_contract_file, _validate_journal_file)
    _validate_existing_record(
        project.events_log,
        lambda path: _validate_jsonl_file(path, "event"),
    )
    _validate_existing_record(project.rejections_log, _validate_jsonl_file)

    for directory in (
        project.tasks_dir,
        project.artifacts_dir,
        project.reviews_dir,
        project.decisions_dir,
        project.logs_dir,
    ):
        _ensure_directory(directory)

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

    _require_complete_project(project)
    return project
