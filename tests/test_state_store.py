from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import socket
import threading
import time
from types import SimpleNamespace

import pytest
import yaml

import wmb.core.state_store as state_store_module
from wmb.core.project import initialize_project
from wmb.core.state_store import (
    IllegalTransition,
    StateConsistencyError,
    StateStore,
)

FORWARD_STATUSES = [
    "intake",
    "awaiting_research_direction",
    "evidence_and_analysis",
    "result_and_claim_build",
    "manuscript_drafting",
    "independent_review",
    "package_verification",
    "awaiting_final_confirmation",
    "candidate_level_4",
]


def _events(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _advance_to(store: StateStore, status: str) -> None:
    for to_status in FORWARD_STATUSES[1 : FORWARD_STATUSES.index(status) + 1]:
        store.transition(
            actor="orchestrator",
            to_status=to_status,
            decision="PROCEED",
            reason="gate passed",
        )


def _put_in_status(store: StateStore, status: str) -> None:
    if status in FORWARD_STATUSES:
        _advance_to(store, status)
    elif status == "downgraded":
        store.transition(
            actor="orchestrator",
            to_status="downgraded",
            decision="DOWNGRADE",
            reason="lower-level outcome selected",
            deliverable="monitoring baseline",
        )
    elif status == "blocked":
        store.transition(
            actor="orchestrator",
            to_status="blocked",
            decision="BLOCK",
            reason="workflow blocked",
            unblock_conditions=["provide required evidence"],
        )


def test_state_store_appends_event_for_legal_transition(tmp_path: Path):
    project = initialize_project(tmp_path)
    store = StateStore(project)

    event = store.transition(
        actor="orchestrator",
        to_status="awaiting_research_direction",
        decision="PROCEED",
        reason="data contract reconciled",
        task_ids=["task-1"],
        artifact_ids=["artifact-1"],
    )

    assert event["from_status"] == "intake"
    assert event["to_status"] == "awaiting_research_direction"
    assert event["decision"] == "PROCEED"
    assert event["run_id"] == store.load_run()["run_id"]
    assert event["task_ids"] == ["task-1"]
    assert event["artifact_ids"] == ["artifact-1"]
    assert store.load_run()["status"] == "awaiting_research_direction"
    assert _events(project.events_log) == [event]
    assert store.audit()["event_count"] == 1


@pytest.mark.parametrize(
    ("from_status", "to_status"),
    [
        ("intake", "awaiting_research_direction"),
        ("awaiting_research_direction", "evidence_and_analysis"),
        ("evidence_and_analysis", "result_and_claim_build"),
        ("result_and_claim_build", "manuscript_drafting"),
        ("manuscript_drafting", "independent_review"),
        ("independent_review", "package_verification"),
        ("package_verification", "awaiting_final_confirmation"),
        ("awaiting_final_confirmation", "candidate_level_4"),
    ],
)
def test_proceed_accepts_each_forward_workflow_transition(
    tmp_path: Path,
    from_status: str,
    to_status: str,
):
    project = initialize_project(tmp_path)
    store = StateStore(project)
    _advance_to(store, from_status)

    event = store.transition(
        actor="orchestrator",
        to_status=to_status,
        decision="PROCEED",
        reason="gate passed",
    )

    assert event["from_status"] == from_status
    assert event["to_status"] == to_status


@pytest.mark.parametrize(
    ("from_status", "to_status"),
    [
        ("intake", "candidate_level_4"),
        ("awaiting_research_direction", "manuscript_drafting"),
        ("candidate_level_4", "intake"),
        ("downgraded", "blocked"),
        ("blocked", "intake"),
    ],
)
def test_illegal_transition_is_rejected_without_state_change(
    tmp_path: Path,
    from_status: str,
    to_status: str,
):
    project = initialize_project(tmp_path)
    store = StateStore(project)
    _put_in_status(store, from_status)
    before = project.run_file.read_bytes()
    before_events = project.events_log.read_bytes()

    with pytest.raises(IllegalTransition):
        store.transition(
            actor="orchestrator",
            to_status=to_status,
            decision="PROCEED",
            reason="tried to skip gates",
        )

    assert project.run_file.read_bytes() == before
    assert project.events_log.read_bytes() == before_events


def test_only_orchestrator_can_transition_canonical_state(tmp_path: Path):
    project = initialize_project(tmp_path)
    before = project.run_file.read_bytes()

    with pytest.raises(IllegalTransition, match="orchestrator"):
        StateStore(project).transition(
            actor="worker",
            to_status="awaiting_research_direction",
            decision="PROCEED",
            reason="worker recommendation",
        )

    assert project.run_file.read_bytes() == before
    assert _events(project.events_log) == []


@pytest.mark.parametrize("decision", ["", "proceed", "PIVOT", None, []])
def test_invalid_decision_is_rejected_without_state_change(
    tmp_path: Path,
    decision,
):
    project = initialize_project(tmp_path)
    before = project.run_file.read_bytes()

    with pytest.raises(IllegalTransition, match="decision"):
        StateStore(project).transition(
            actor="orchestrator",
            to_status="awaiting_research_direction",
            decision=decision,
            reason="gate passed",
        )

    assert project.run_file.read_bytes() == before
    assert _events(project.events_log) == []


@pytest.mark.parametrize("reason", ["", "   ", None])
def test_empty_reason_is_rejected_without_state_change(tmp_path: Path, reason):
    project = initialize_project(tmp_path)
    before = project.run_file.read_bytes()

    with pytest.raises(IllegalTransition, match="reason"):
        StateStore(project).transition(
            actor="orchestrator",
            to_status="awaiting_research_direction",
            decision="PROCEED",
            reason=reason,
        )

    assert project.run_file.read_bytes() == before
    assert _events(project.events_log) == []


@pytest.mark.parametrize("unblock_conditions", [None, [], ["   "]])
def test_block_requires_explicit_nonempty_unblock_conditions(
    tmp_path: Path,
    unblock_conditions,
):
    project = initialize_project(tmp_path)

    with pytest.raises(IllegalTransition, match="unblock_conditions"):
        StateStore(project).transition(
            actor="orchestrator",
            to_status="blocked",
            decision="BLOCK",
            reason="source data conflict",
            unblock_conditions=unblock_conditions,
        )

    assert StateStore(project).load_run()["status"] == "intake"
    assert _events(project.events_log) == []


def test_block_records_unblock_conditions(tmp_path: Path):
    project = initialize_project(tmp_path)

    event = StateStore(project).transition(
        actor="orchestrator",
        to_status="blocked",
        decision="BLOCK",
        reason="source data conflict",
        unblock_conditions=["reconcile sample counts"],
    )

    assert event["unblock_conditions"] == ["reconcile sample counts"]
    assert StateStore(project).load_run()["status"] == "blocked"


@pytest.mark.parametrize("deliverable", [None, "", "   "])
def test_downgrade_requires_explicit_nonempty_deliverable(
    tmp_path: Path,
    deliverable,
):
    project = initialize_project(tmp_path)

    with pytest.raises(IllegalTransition, match="deliverable"):
        StateStore(project).transition(
            actor="orchestrator",
            to_status="downgraded",
            decision="DOWNGRADE",
            reason="no answerable research question",
            deliverable=deliverable,
        )

    assert StateStore(project).load_run()["status"] == "intake"
    assert _events(project.events_log) == []


def test_downgrade_records_smallest_defensible_deliverable(tmp_path: Path):
    project = initialize_project(tmp_path)

    event = StateStore(project).transition(
        actor="orchestrator",
        to_status="downgraded",
        decision="DOWNGRADE",
        reason="no answerable research question",
        deliverable="monitoring baseline",
    )

    assert event["deliverable"] == "monitoring baseline"
    assert StateStore(project).load_run()["status"] == "downgraded"


def test_refine_returns_independent_review_to_drafting(tmp_path: Path):
    project = initialize_project(tmp_path)
    store = StateStore(project)
    _advance_to(store, "independent_review")

    event = store.transition(
        actor="orchestrator",
        to_status="manuscript_drafting",
        decision="REFINE",
        reason="review identified bounded revisions",
    )

    assert event["decision"] == "REFINE"
    assert store.load_run()["status"] == "manuscript_drafting"


def test_decision_must_match_transition_target(tmp_path: Path):
    project = initialize_project(tmp_path)

    with pytest.raises(IllegalTransition, match="not legal"):
        StateStore(project).transition(
            actor="orchestrator",
            to_status="blocked",
            decision="PROCEED",
            reason="mismatched decision",
            unblock_conditions=["provide data"],
        )

    assert StateStore(project).load_run()["status"] == "intake"
    assert _events(project.events_log) == []


def test_run_write_failure_does_not_append_event(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    project = initialize_project(tmp_path)
    store = StateStore(project)
    before = project.run_file.read_bytes()

    def fail_run_write(_run):
        raise OSError("simulated run write failure")

    monkeypatch.setattr(store, "_write_run", fail_run_write)

    with pytest.raises(OSError, match="run write failure"):
        store.transition(
            actor="orchestrator",
            to_status="awaiting_research_direction",
            decision="PROCEED",
            reason="gate passed",
        )

    assert project.run_file.read_bytes() == before
    assert _events(project.events_log) == []


def test_event_append_failure_rolls_back_run(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    project = initialize_project(tmp_path)
    store = StateStore(project)
    before = project.run_file.read_bytes()

    def fail_event_append(_event):
        raise OSError("simulated event append failure")

    monkeypatch.setattr(store, "_append_event", fail_event_append)

    with pytest.raises(OSError, match="event append failure"):
        store.transition(
            actor="orchestrator",
            to_status="awaiting_research_direction",
            decision="PROCEED",
            reason="gate passed",
        )

    assert project.run_file.read_bytes() == before
    assert _events(project.events_log) == []
    assert store.audit()["status"] == "intake"


def test_pending_transition_is_recovered_after_failed_rollback(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    project = initialize_project(tmp_path)
    store = StateStore(project)
    real_write_run = store._write_run
    writes = 0

    def fail_rollback(run):
        nonlocal writes
        writes += 1
        if writes == 2:
            raise OSError("simulated rollback failure")
        real_write_run(run)

    def fail_event_append(_event):
        raise OSError("simulated event append failure")

    monkeypatch.setattr(store, "_write_run", fail_rollback)
    monkeypatch.setattr(store, "_append_event", fail_event_append)

    with pytest.raises(StateConsistencyError, match="pending_transition.json"):
        store.transition(
            actor="orchestrator",
            to_status="awaiting_research_direction",
            decision="PROCEED",
            reason="gate passed",
        )

    assert (project.logs_dir / "pending_transition.json").is_file()
    assert StateStore(project).load_run()["status"] == "intake"
    assert not (project.logs_dir / "pending_transition.json").exists()
    assert _events(project.events_log) == []


def test_writer_lock_records_owner_and_releases_only_unchanged_lock(tmp_path: Path):
    store = StateStore(initialize_project(tmp_path))

    with store._locked():
        lock = json.loads(store._lock_path.read_text(encoding="utf-8"))
        assert lock["pid"] == os.getpid()
        assert lock["host"] == socket.gethostname()
        assert lock["token"]
        replacement = {**lock, "token": "replacement-owner"}
        store._lock_path.write_text(json.dumps(replacement), encoding="utf-8")

    assert json.loads(store._lock_path.read_text(encoding="utf-8")) == replacement
    store._lock_path.unlink()


def test_owned_lock_release_retries_transient_permission_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    store = StateStore(initialize_project(tmp_path))
    real_unlink = Path.unlink
    attempts = 0

    def transient_unlink(path, *args, **kwargs):
        nonlocal attempts
        if path == store._lock_path:
            attempts += 1
            if attempts < 3:
                raise PermissionError("simulated Windows sharing contention")
        return real_unlink(path, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", transient_unlink)

    with store._locked():
        pass

    assert attempts == 3
    assert not store._lock_path.exists()


def test_owned_lock_release_stops_after_bounded_permission_errors(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    store = StateStore(initialize_project(tmp_path))
    real_unlink = Path.unlink
    attempts = 0
    clock = 0.0

    def blocked_unlink(path, *args, **kwargs):
        nonlocal attempts
        if path == store._lock_path:
            attempts += 1
            raise PermissionError("simulated persistent Windows sharing contention")
        return real_unlink(path, *args, **kwargs)

    def monotonic():
        return clock

    def sleep(seconds):
        nonlocal clock
        clock += seconds

    monkeypatch.setattr(Path, "unlink", blocked_unlink)
    monkeypatch.setattr(
        state_store_module,
        "time",
        SimpleNamespace(monotonic=monotonic, sleep=sleep, time=time.time),
    )
    monkeypatch.setattr(state_store_module, "_LOCK_RELEASE_TIMEOUT_SECONDS", 0.003)
    monkeypatch.setattr(state_store_module, "_LOCK_RELEASE_DELAY_SECONDS", 0.001)

    with store._locked():
        pass

    assert attempts == 4
    assert clock == pytest.approx(0.003)
    assert store._lock_path.exists()
    real_unlink(store._lock_path)


def test_owned_lock_release_rechecks_ownership_before_retry(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    store = StateStore(initialize_project(tmp_path))
    real_unlink = Path.unlink
    attempts = 0
    replacement: dict[str, object] = {}

    def replace_then_block(path, *args, **kwargs):
        nonlocal attempts, replacement
        if path == store._lock_path:
            attempts += 1
            owner = json.loads(path.read_text(encoding="utf-8"))
            replacement = {**owner, "token": "replacement-owner"}
            path.write_text(json.dumps(replacement), encoding="utf-8")
            raise PermissionError("replacement arrived during sharing contention")
        return real_unlink(path, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", replace_then_block)

    with store._locked():
        pass

    assert attempts == 1
    assert json.loads(store._lock_path.read_text(encoding="utf-8")) == replacement
    real_unlink(store._lock_path)


def test_writer_acquisition_retries_transient_permission_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    store = StateStore(initialize_project(tmp_path))
    real_open = os.open
    attempts = 0

    def transient_open(path, flags, mode=0o777, *, dir_fd=None):
        nonlocal attempts
        if Path(path) == store._lock_path:
            attempts += 1
            if attempts < 3:
                raise PermissionError("simulated Windows sharing contention")
        return real_open(path, flags, mode, dir_fd=dir_fd)

    monkeypatch.setattr(state_store_module.os, "open", transient_open)

    with store._locked():
        pass

    assert attempts == 3
    assert not store._lock_path.exists()


def test_failed_lock_record_write_releases_unchanged_owned_lock(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    store = StateStore(initialize_project(tmp_path))
    real_write_descriptor = state_store_module._write_descriptor

    def fail_after_write(descriptor, content):
        real_write_descriptor(descriptor, content)
        raise OSError("simulated lock fsync failure")

    monkeypatch.setattr(state_store_module, "_write_descriptor", fail_after_write)

    with pytest.raises(OSError, match="lock fsync failure"):
        with store._locked():
            pass

    assert not store._lock_path.exists()


@pytest.mark.parametrize("_iteration", range(10))
def test_slow_live_writer_lock_is_not_stolen_by_concurrent_writer(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    _iteration: int,
):
    project = initialize_project(tmp_path)
    first = StateStore(project)
    second = StateStore(project)
    entered_write = threading.Event()
    release_write = threading.Event()
    real_write_run = first._write_run

    monkeypatch.setattr(state_store_module, "_LOCK_STALE_SECONDS", 0.01)
    monkeypatch.setattr(state_store_module, "_LOCK_ATTEMPTS", 5_000)

    def slow_write(run):
        entered_write.set()
        assert release_write.wait(timeout=2)
        real_write_run(run)

    monkeypatch.setattr(first, "_write_run", slow_write)

    with ThreadPoolExecutor(max_workers=2) as executor:
        first_write = executor.submit(
            first.transition,
            actor="orchestrator",
            to_status="awaiting_research_direction",
            decision="PROCEED",
            reason="slow writer owns the lock",
        )
        assert entered_write.wait(timeout=1)
        second_write = executor.submit(
            second.transition,
            actor="orchestrator",
            to_status="awaiting_research_direction",
            decision="PROCEED",
            reason="concurrent writer must wait",
        )
        try:
            time.sleep(0.05)
            assert not second_write.done()
        finally:
            release_write.set()

        first_write.result(timeout=2)
        with pytest.raises(IllegalTransition):
            second_write.result(timeout=2)

    assert StateStore(project).audit()["event_count"] == 1


def test_stale_foreign_host_lock_is_not_recovered_without_proof_owner_is_dead(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    store = StateStore(initialize_project(tmp_path))
    lock = {
        "pid": 2_147_483_647,
        "host": "unreachable-foreign-host",
        "created_at": 0,
        "token": "foreign-owner",
    }
    store._lock_path.write_text(json.dumps(lock), encoding="utf-8")
    os.utime(store._lock_path, (0, 0))
    monkeypatch.setattr(state_store_module, "_LOCK_ATTEMPTS", 3)
    monkeypatch.setattr(state_store_module, "_LOCK_DELAY_SECONDS", 0.001)
    monkeypatch.setattr(state_store_module, "_LOCK_STALE_SECONDS", 0)

    with pytest.raises(TimeoutError):
        with store._locked():
            pass

    assert json.loads(store._lock_path.read_text(encoding="utf-8")) == lock
    store._lock_path.unlink()


def test_stale_dead_same_host_lock_is_recovered(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    store = StateStore(initialize_project(tmp_path))
    lock = {
        "pid": 2_147_483_647,
        "host": socket.gethostname(),
        "created_at": 0,
        "token": "dead-owner",
    }
    store._lock_path.write_text(json.dumps(lock), encoding="utf-8")
    os.utime(store._lock_path, (0, 0))
    monkeypatch.setattr(state_store_module, "_LOCK_STALE_SECONDS", 0)

    with store._locked():
        current = json.loads(store._lock_path.read_text(encoding="utf-8"))
        assert current["token"] != lock["token"]

    assert not store._lock_path.exists()


def test_stale_invalid_lock_is_recovered(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    store = StateStore(initialize_project(tmp_path))
    store._lock_path.write_text("invalid lock", encoding="utf-8")
    os.utime(store._lock_path, (0, 0))
    monkeypatch.setattr(state_store_module, "_LOCK_STALE_SECONDS", 0)

    with store._locked():
        assert store._lock_path.exists()

    assert not store._lock_path.exists()


def test_tampered_pending_transition_cannot_rewrite_intake_to_candidate_level_4(
    tmp_path: Path,
):
    project = initialize_project(tmp_path)
    store = StateStore(project)
    run_before = project.run_file.read_bytes()
    events_before = project.events_log.read_bytes()
    intake_run = yaml.safe_load(run_before)
    candidate_run = {**intake_run, "status": "candidate_level_4"}
    malicious_event = {
        "event_id": "malicious-event",
        "run_id": intake_run["run_id"],
        "timestamp": "2026-06-13T00:00:00Z",
        "actor": "orchestrator",
        "event_type": "transition",
        "from_status": "candidate_level_4",
        "to_status": "intake",
        "decision": "PROCEED",
        "reason": "tampered rollback payload",
    }
    malicious_event_line = json.dumps(malicious_event, sort_keys=True) + "\n"
    store._pending_path.write_text(
        json.dumps(
            {
                "transaction_id": "malicious-transaction",
                "before_run": candidate_run,
                "projected_run": intake_run,
                "event": malicious_event,
                "events_before": "",
                "events_after": malicious_event_line,
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(StateConsistencyError, match="pending transition"):
        store.load_run()

    assert project.run_file.read_bytes() == run_before
    assert project.events_log.read_bytes() == events_before
    assert store._pending_path.is_file()


def test_pending_recovery_rejects_unproven_event_history_without_changes(
    tmp_path: Path,
):
    project = initialize_project(tmp_path)
    store = StateStore(project)
    intake_run = yaml.safe_load(project.run_file.read_text(encoding="utf-8"))
    projected_run = {**intake_run, "status": "awaiting_research_direction"}
    project.run_file.write_text(
        yaml.safe_dump(projected_run, sort_keys=False),
        encoding="utf-8",
    )
    run_before = project.run_file.read_bytes()
    events_before = project.events_log.read_bytes()
    event = {
        "event_id": "unproven-event",
        "run_id": intake_run["run_id"],
        "timestamp": "2026-06-13T00:00:00Z",
        "actor": "orchestrator",
        "event_type": "transition",
        "from_status": "intake",
        "to_status": "awaiting_research_direction",
        "decision": "PROCEED",
        "reason": "legal event with tampered history",
    }
    store._pending_path.write_text(
        json.dumps(
            {
                "transaction_id": "tampered-history",
                "before_run": intake_run,
                "projected_run": projected_run,
                "event": event,
                "events_before": "",
                "events_after": "",
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(StateConsistencyError, match="exact event append"):
        store.load_run()

    assert project.run_file.read_bytes() == run_before
    assert project.events_log.read_bytes() == events_before
    assert store._pending_path.is_file()


def test_audit_detects_run_event_projection_mismatch(tmp_path: Path):
    project = initialize_project(tmp_path)
    store = StateStore(project)
    store.transition(
        actor="orchestrator",
        to_status="awaiting_research_direction",
        decision="PROCEED",
        reason="gate passed",
    )
    run = store.load_run()
    run["status"] = "evidence_and_analysis"
    project.run_file.write_text(yaml.safe_dump(run, sort_keys=False), encoding="utf-8")

    with pytest.raises(StateConsistencyError, match="projection"):
        store.audit()


def test_transition_rejects_existing_run_event_projection_mismatch(tmp_path: Path):
    project = initialize_project(tmp_path)
    store = StateStore(project)
    store.transition(
        actor="orchestrator",
        to_status="awaiting_research_direction",
        decision="PROCEED",
        reason="gate passed",
    )
    run = store.load_run()
    run["status"] = "evidence_and_analysis"
    project.run_file.write_text(yaml.safe_dump(run, sort_keys=False), encoding="utf-8")
    before_events = project.events_log.read_bytes()

    with pytest.raises(StateConsistencyError, match="projection"):
        store.transition(
            actor="orchestrator",
            to_status="result_and_claim_build",
            decision="PROCEED",
            reason="analysis complete",
        )

    assert project.events_log.read_bytes() == before_events
    assert yaml.safe_load(project.run_file.read_text(encoding="utf-8"))["status"] == (
        "evidence_and_analysis"
    )


def test_audit_rejects_swapped_event_ledgers_from_other_runs(tmp_path: Path):
    first_project = initialize_project(tmp_path / "first")
    second_project = initialize_project(tmp_path / "second")
    first_store = StateStore(first_project)
    second_store = StateStore(second_project)
    for store in (first_store, second_store):
        store.transition(
            actor="orchestrator",
            to_status="awaiting_research_direction",
            decision="PROCEED",
            reason="gate passed",
        )
    first_events = first_project.events_log.read_bytes()
    second_events = second_project.events_log.read_bytes()
    first_project.events_log.write_bytes(second_events)
    second_project.events_log.write_bytes(first_events)

    with pytest.raises(StateConsistencyError, match="run_id"):
        first_store.audit()
    with pytest.raises(StateConsistencyError, match="run_id"):
        second_store.audit()


def test_audit_rejects_duplicate_event_id(tmp_path: Path):
    project = initialize_project(tmp_path)
    store = StateStore(project)
    _advance_to(store, "evidence_and_analysis")
    events = _events(project.events_log)
    events[1]["event_id"] = events[0]["event_id"]
    project.events_log.write_text(
        "".join(json.dumps(event) + "\n" for event in events),
        encoding="utf-8",
    )

    with pytest.raises(StateConsistencyError, match="duplicate event_id"):
        store.audit()


def test_audit_rejects_event_without_decision(tmp_path: Path):
    project = initialize_project(tmp_path)
    run = yaml.safe_load(project.run_file.read_text(encoding="utf-8"))
    run["status"] = "awaiting_research_direction"
    project.run_file.write_text(yaml.safe_dump(run, sort_keys=False), encoding="utf-8")
    project.events_log.write_text(
        json.dumps(
            {
                "event_id": "legacy-event",
                "run_id": run["run_id"],
                "timestamp": "2026-06-13T00:00:00Z",
                "actor": "orchestrator",
                "event_type": "transition",
                "from_status": "intake",
                "to_status": "awaiting_research_direction",
                "reason": "legacy event missing decision",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(StateConsistencyError, match="decision"):
        StateStore(project).audit()


def test_audit_rejects_event_with_whitespace_reason(tmp_path: Path):
    project = initialize_project(tmp_path)
    run = yaml.safe_load(project.run_file.read_text(encoding="utf-8"))
    run["status"] = "awaiting_research_direction"
    project.run_file.write_text(yaml.safe_dump(run, sort_keys=False), encoding="utf-8")
    project.events_log.write_text(
        json.dumps(
            {
                "event_id": "invalid-reason-event",
                "run_id": run["run_id"],
                "timestamp": "2026-06-13T00:00:00Z",
                "actor": "orchestrator",
                "event_type": "transition",
                "from_status": "intake",
                "to_status": "awaiting_research_direction",
                "decision": "PROCEED",
                "reason": "   ",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(StateConsistencyError, match="reason"):
        StateStore(project).audit()


def test_audit_rejects_decision_that_does_not_authorize_transition(tmp_path: Path):
    project = initialize_project(tmp_path)
    run = yaml.safe_load(project.run_file.read_text(encoding="utf-8"))
    run["status"] = "awaiting_research_direction"
    project.run_file.write_text(yaml.safe_dump(run, sort_keys=False), encoding="utf-8")
    project.events_log.write_text(
        json.dumps(
            {
                "event_id": "mismatched-decision-event",
                "run_id": run["run_id"],
                "timestamp": "2026-06-13T00:00:00Z",
                "actor": "orchestrator",
                "event_type": "transition",
                "from_status": "intake",
                "to_status": "awaiting_research_direction",
                "decision": "REFINE",
                "reason": "decision does not authorize target",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(StateConsistencyError, match="illegal transition"):
        StateStore(project).audit()
