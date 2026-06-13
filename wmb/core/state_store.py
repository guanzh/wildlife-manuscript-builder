"""Transactional single writer for canonical WMB workflow state."""

from __future__ import annotations

import json
import math
import os
import socket
import time
from collections.abc import Iterable, Mapping
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any
from uuid import uuid4

import yaml

from wmb.contracts import ContractError, validate_contract
from wmb.core.models import ProjectPaths
from wmb.core.state_machine import (
    IllegalTransition,
    validate_transition,
)

_LOCK_ATTEMPTS = 1_000
_LOCK_DELAY_SECONDS = 0.001
_LOCK_RELEASE_DELAY_SECONDS = 0.001
_LOCK_RELEASE_TIMEOUT_SECONDS = 1.0
_LOCK_STALE_SECONDS = 30.0


class StateConsistencyError(RuntimeError):
    """Raised when canonical run state and its event projection disagree."""


def _exclusive_flags() -> int:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_BINARY"):
        flags |= os.O_BINARY
    return flags


def _write_descriptor(descriptor: int, content: bytes) -> None:
    written = 0
    while written < len(content):
        count = os.write(descriptor, content[written:])
        if count == 0:
            raise OSError("zero-byte write while acquiring state writer lock")
        written += count
    os.fsync(descriptor)


def _lock_snapshot(lock_path: Path) -> tuple[bytes, tuple[int, int], float] | None:
    try:
        with lock_path.open("rb") as lock_file:
            stat = os.fstat(lock_file.fileno())
            return (
                lock_file.read(),
                (stat.st_dev, stat.st_ino),
                stat.st_mtime,
            )
    except FileNotFoundError:
        return None


def _remove_lock_if_unchanged(
    lock_path: Path,
    expected_data: bytes,
    expected_identity: tuple[int, int],
) -> bool:
    deadline = time.monotonic() + _LOCK_RELEASE_TIMEOUT_SECONDS
    while True:
        try:
            snapshot = _lock_snapshot(lock_path)
        except PermissionError:
            pass
        else:
            if snapshot is None or snapshot[:2] != (
                expected_data,
                expected_identity,
            ):
                return False
            try:
                lock_path.unlink()
            except FileNotFoundError:
                return False
            except PermissionError:
                pass
            else:
                return True

        if time.monotonic() >= deadline:
            return False
        time.sleep(_LOCK_RELEASE_DELAY_SECONDS)


def _lock_owner(lock_data: bytes) -> tuple[int, str, str] | None:
    try:
        payload = json.loads(lock_data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    pid = payload.get("pid")
    host = payload.get("host")
    token = payload.get("token")
    created_at = payload.get("created_at")
    if (
        isinstance(pid, bool)
        or not isinstance(pid, int)
        or pid <= 0
        or not isinstance(host, str)
        or not host.strip()
        or not isinstance(token, str)
        or not token.strip()
        or isinstance(created_at, bool)
        or not isinstance(created_at, (int, float))
        or not math.isfinite(created_at)
    ):
        return None
    return pid, host, token


def _pid_is_alive(pid: int) -> bool | None:
    if pid == os.getpid():
        return True
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes

        process_query_limited_information = 0x1000
        error_access_denied = 5
        error_invalid_parameter = 87
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.OpenProcess.argtypes = [
            wintypes.DWORD,
            wintypes.BOOL,
            wintypes.DWORD,
        ]
        kernel32.OpenProcess.restype = wintypes.HANDLE
        kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel32.CloseHandle.restype = wintypes.BOOL
        handle = kernel32.OpenProcess(
            process_query_limited_information,
            False,
            pid,
        )
        if handle:
            kernel32.CloseHandle(handle)
            return True
        error = ctypes.get_last_error()
        if error == error_invalid_parameter:
            return False
        if error == error_access_denied:
            return True
        return None

    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return None
    return True


def _stale_lock_is_recoverable(
    lock_data: bytes,
    modified_at: float,
) -> bool:
    if time.time() - modified_at < _LOCK_STALE_SECONDS:
        return False
    owner = _lock_owner(lock_data)
    if owner is None:
        return True
    pid, host, _ = owner
    return host == socket.gethostname() and _pid_is_alive(pid) is False


def _atomic_write_text(path: Path, content: str) -> None:
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
        os.replace(temporary_path, path)
        temporary_path = None
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def _yaml_text(payload: Mapping[str, Any]) -> str:
    return yaml.safe_dump(dict(payload), allow_unicode=True, sort_keys=False)


def _event_line(event: Mapping[str, Any]) -> str:
    return json.dumps(dict(event), ensure_ascii=False, sort_keys=True) + "\n"


def _nonblank(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise IllegalTransition(f"{field} must be a non-blank string")
    return value.strip()


def _identifier_list(values: object, field: str) -> list[str]:
    if values is None:
        return []
    if isinstance(values, str) or not isinstance(values, Iterable):
        raise IllegalTransition(f"{field} must be a list of non-blank strings")
    normalized = [_nonblank(value, field) for value in values]
    return normalized


def _conditions(values: object) -> list[str]:
    if isinstance(values, str):
        values = [values]
    conditions = _identifier_list(values, "unblock_conditions")
    if not conditions:
        raise IllegalTransition("BLOCK requires non-empty unblock_conditions")
    return conditions


def _load_jsonl(content: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(content.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise StateConsistencyError(
                f"invalid event JSON at line {line_number}"
            ) from exc
        if not isinstance(record, dict):
            raise StateConsistencyError(
                f"event at line {line_number} is not an object"
            )
        try:
            validate_contract("event", record)
        except ContractError as exc:
            raise StateConsistencyError(
                f"invalid event at line {line_number}: {exc}"
            ) from exc
        records.append(record)
    return records


class StateStore:
    """The only component allowed to change canonical workflow state."""

    def __init__(self, project: ProjectPaths) -> None:
        if not isinstance(project, ProjectPaths):
            raise TypeError("project must be ProjectPaths")
        self.project = project
        self._lock_path = project.wmb_dir / ".state-store.lock"
        self._pending_path = project.logs_dir / "pending_transition.json"

    def load_run(self) -> dict[str, Any]:
        """Load the validated run projection after recovering interrupted work."""

        with self._locked():
            self._recover_pending_locked()
            return self._load_run_locked()

    def transition(
        self,
        *,
        actor: str,
        to_status: str,
        decision: str,
        reason: str,
        unblock_conditions: Iterable[str] | str | None = None,
        deliverable: str | None = None,
        task_ids: Iterable[str] | None = None,
        artifact_ids: Iterable[str] | None = None,
    ) -> dict[str, Any]:
        """Validate and transactionally persist one canonical transition."""

        if actor != "orchestrator":
            raise IllegalTransition(
                "only actor='orchestrator' may transition canonical state"
            )
        reason = _nonblank(reason, "reason")
        normalized_task_ids = _identifier_list(task_ids, "task_ids")
        normalized_artifact_ids = _identifier_list(artifact_ids, "artifact_ids")

        with self._locked():
            self._recover_pending_locked()
            run = self._load_run_locked()
            self._audit_locked(run)
            validate_transition(run["status"], to_status, decision)

            event: dict[str, Any] = {
                "event_id": f"event-{uuid4().hex}",
                "run_id": run["run_id"],
                "timestamp": datetime.now(timezone.utc)
                .isoformat()
                .replace("+00:00", "Z"),
                "actor": actor,
                "event_type": "transition",
                "from_status": run["status"],
                "to_status": to_status,
                "decision": decision,
                "reason": reason,
            }
            if normalized_task_ids:
                event["task_ids"] = normalized_task_ids
            if normalized_artifact_ids:
                event["artifact_ids"] = normalized_artifact_ids
            if decision == "BLOCK":
                event["unblock_conditions"] = _conditions(unblock_conditions)
            elif unblock_conditions is not None:
                raise IllegalTransition(
                    "unblock_conditions may only accompany a BLOCK decision"
                )
            if decision == "DOWNGRADE":
                event["deliverable"] = _nonblank(deliverable, "deliverable")
            elif deliverable is not None:
                raise IllegalTransition(
                    "deliverable may only accompany a DOWNGRADE decision"
                )

            projected_run = {**run, "status": to_status}
            validate_contract("run", projected_run)
            validate_contract("event", event)

            events_before = self.project.events_log.read_text(encoding="utf-8")
            _load_jsonl(events_before)
            transaction = {
                "transaction_id": f"transaction-{uuid4().hex}",
                "before_run": run,
                "projected_run": projected_run,
                "event": event,
                "events_before": events_before,
                "events_after": events_before + _event_line(event),
            }
            self._write_pending(transaction)

            try:
                self._write_run(projected_run)
                self._append_event(event)
            except Exception:
                try:
                    self._rollback_locked(transaction)
                except Exception as rollback_exc:
                    raise StateConsistencyError(
                        "transition failed and automatic rollback could not "
                        f"restore canonical state; recover from {self._pending_path}"
                    ) from rollback_exc
                raise

            self._clear_pending()
            return event

    def audit(self) -> dict[str, Any]:
        """Validate the event chain and its projection onto ``run.yaml``."""

        with self._locked():
            self._recover_pending_locked()
            run = self._load_run_locked()
            events = self._audit_locked(run)
            return {
                "status": run["status"],
                "event_count": len(events),
                "latest_event_id": events[-1]["event_id"] if events else None,
            }

    def _audit_locked(self, run: Mapping[str, Any]) -> list[dict[str, Any]]:
        return self._audit_snapshot(
            run,
            self.project.events_log.read_text(encoding="utf-8"),
        )

    def _audit_snapshot(
        self,
        run: Mapping[str, Any],
        event_content: str,
    ) -> list[dict[str, Any]]:
        events = _load_jsonl(event_content)
        if not events and run["status"] != "intake":
            raise StateConsistencyError(
                "run projection has no events and is not in the initial intake state"
            )

        previous_to: object | None = None
        event_ids: set[str] = set()
        for index, event in enumerate(events):
            if event["run_id"] != run["run_id"]:
                raise StateConsistencyError(
                    "event ledger run_id does not match the canonical run"
                )
            if event["event_id"] in event_ids:
                raise StateConsistencyError(
                    f"duplicate event_id in event ledger: {event['event_id']}"
                )
            event_ids.add(event["event_id"])
            if index == 0 and event["from_status"] != "intake":
                raise StateConsistencyError(
                    "event ledger does not begin from the initial intake state"
                )
            if previous_to is not None and event["from_status"] != previous_to:
                raise StateConsistencyError("event ledger transition chain is broken")
            try:
                self._validate_event_policy(event)
            except IllegalTransition as exc:
                raise StateConsistencyError(
                    f"event ledger contains an illegal transition: {exc}"
                ) from exc
            previous_to = event["to_status"]

        if events and events[-1]["to_status"] != run["status"]:
            raise StateConsistencyError(
                "run projection does not match the latest event"
            )
        return events

    def _validate_event_policy(self, event: Mapping[str, Any]) -> None:
        if event["actor"] != "orchestrator":
            raise IllegalTransition(
                "only actor='orchestrator' may transition canonical state"
            )
        if event["event_type"] != "transition":
            raise IllegalTransition("canonical state events must be transitions")
        _nonblank(event["reason"], "reason")
        validate_transition(
            event["from_status"],
            event["to_status"],
            event["decision"],
        )
        if event["decision"] == "BLOCK":
            _conditions(event.get("unblock_conditions"))
        elif "unblock_conditions" in event:
            raise IllegalTransition(
                "unblock_conditions may only accompany a BLOCK decision"
            )
        if event["decision"] == "DOWNGRADE":
            _nonblank(event.get("deliverable"), "deliverable")
        elif "deliverable" in event:
            raise IllegalTransition(
                "deliverable may only accompany a DOWNGRADE decision"
            )

    def _load_run_locked(self) -> dict[str, Any]:
        payload = yaml.safe_load(self.project.run_file.read_text(encoding="utf-8"))
        validate_contract("run", payload)
        return dict(payload)

    def _write_run(self, run: Mapping[str, Any]) -> None:
        _atomic_write_text(self.project.run_file, _yaml_text(run))

    def _append_event(self, event: Mapping[str, Any]) -> None:
        before = self.project.events_log.read_text(encoding="utf-8")
        _load_jsonl(before)
        _atomic_write_text(self.project.events_log, before + _event_line(event))

    def _write_pending(self, transaction: Mapping[str, Any]) -> None:
        content = json.dumps(dict(transaction), ensure_ascii=False, sort_keys=True)
        _atomic_write_text(self._pending_path, content + "\n")

    def _load_pending(self) -> dict[str, Any]:
        try:
            payload = json.loads(self._pending_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            raise StateConsistencyError(
                f"cannot read pending transition journal: {self._pending_path}"
            ) from exc
        required = {
            "before_run",
            "projected_run",
            "event",
            "events_before",
            "events_after",
        }
        if not isinstance(payload, dict) or not required.issubset(payload):
            raise StateConsistencyError("pending transition journal is incomplete")
        self._validate_pending_transaction(payload)
        return payload

    def _validate_pending_transaction(self, transaction: Mapping[str, Any]) -> None:
        try:
            before_run = transaction["before_run"]
            projected_run = transaction["projected_run"]
            event = transaction["event"]
            events_before = transaction["events_before"]
            events_after = transaction["events_after"]
            validate_contract("run", before_run)
            validate_contract("run", projected_run)
            validate_contract("event", event)
            self._validate_event_policy(event)
            if event["from_status"] != before_run["status"]:
                raise StateConsistencyError(
                    "pending event does not start from before_run"
                )
            expected_projection = {**before_run, "status": event["to_status"]}
            if projected_run != expected_projection:
                raise StateConsistencyError(
                    "pending projected_run is not the event projection"
                )
            if events_after != events_before + _event_line(event):
                raise StateConsistencyError(
                    "pending events_after is not the exact event append"
                )
            self._audit_snapshot(before_run, events_before)
            self._audit_snapshot(projected_run, events_after)
        except (
            ContractError,
            IllegalTransition,
            KeyError,
            TypeError,
        ) as exc:
            raise StateConsistencyError(
                f"pending transition journal is inconsistent: {exc}"
            ) from exc

    def _recover_pending_locked(self) -> None:
        if not self._pending_path.exists():
            return
        transaction = self._load_pending()
        run = self._load_run_locked()
        events = self.project.events_log.read_text(encoding="utf-8")
        if (
            run == transaction["projected_run"]
            and events == transaction["events_after"]
        ):
            self._clear_pending()
            return
        if run == transaction["before_run"] and events == transaction["events_before"]:
            self._clear_pending()
            return
        if (
            run == transaction["projected_run"]
            and events == transaction["events_before"]
        ):
            self._rollback_locked(transaction)
            return
        raise StateConsistencyError(
            "pending transition does not match a recoverable write phase; "
            "canonical state was not changed"
        )

    def _rollback_locked(self, transaction: Mapping[str, Any]) -> None:
        self._validate_pending_transaction(transaction)
        run = self._load_run_locked()
        events = self.project.events_log.read_text(encoding="utf-8")
        valid_runs = (transaction["before_run"], transaction["projected_run"])
        valid_events = (transaction["events_before"], transaction["events_after"])
        if run not in valid_runs or events not in valid_events:
            raise StateConsistencyError(
                "pending transition does not match canonical files; manual audit required"
            )
        if events != transaction["events_before"]:
            _atomic_write_text(self.project.events_log, transaction["events_before"])
        if run != transaction["before_run"]:
            self._write_run(transaction["before_run"])
        self._clear_pending()

    def _clear_pending(self) -> None:
        self._pending_path.unlink(missing_ok=True)

    @contextmanager
    def _locked(self):
        lock_data = json.dumps(
            {
                "pid": os.getpid(),
                "host": socket.gethostname(),
                "created_at": time.time(),
                "token": uuid4().hex,
            },
            sort_keys=True,
        ).encode("utf-8")
        lock_identity: tuple[int, int] | None = None
        for _ in range(_LOCK_ATTEMPTS):
            try:
                descriptor = os.open(
                    self._lock_path,
                    _exclusive_flags(),
                    0o600,
                )
            except (FileExistsError, PermissionError):
                try:
                    snapshot = _lock_snapshot(self._lock_path)
                except PermissionError:
                    time.sleep(_LOCK_DELAY_SECONDS)
                    continue
                if snapshot is None:
                    time.sleep(_LOCK_DELAY_SECONDS)
                    continue
                existing_data, existing_identity, modified_at = snapshot
                if _stale_lock_is_recoverable(existing_data, modified_at):
                    _remove_lock_if_unchanged(
                        self._lock_path,
                        existing_data,
                        existing_identity,
                    )
                    continue
                time.sleep(_LOCK_DELAY_SECONDS)
                continue
            created = os.fstat(descriptor)
            created_identity = (created.st_dev, created.st_ino)
            try:
                _write_descriptor(descriptor, lock_data)
            except Exception:
                try:
                    os.close(descriptor)
                except OSError:
                    pass
                _remove_lock_if_unchanged(
                    self._lock_path,
                    lock_data,
                    created_identity,
                )
                raise
            try:
                os.close(descriptor)
            except Exception:
                _remove_lock_if_unchanged(
                    self._lock_path,
                    lock_data,
                    created_identity,
                )
                raise
            lock_identity = created_identity
            break
        if lock_identity is None:
            raise TimeoutError("timed out acquiring canonical state writer lock")

        try:
            yield
        finally:
            _remove_lock_if_unchanged(
                self._lock_path,
                lock_data,
                lock_identity,
            )


__all__ = ["IllegalTransition", "StateConsistencyError", "StateStore"]
