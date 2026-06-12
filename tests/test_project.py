import errno
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Event

import pytest
import yaml

from wmb.contracts import ContractError, validate_contract
from wmb.core import project as project_module
from wmb.core.models import ProjectPaths
from wmb.core.project import InitializationError, initialize_project


def _load_yaml(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_initialize_project_creates_default_state(tmp_path: Path):
    project = initialize_project(tmp_path)

    run = _load_yaml(project.run_file)
    author_queue = _load_yaml(project.author_confirmation_queue_file)
    journal = _load_yaml(project.journal_contract_file)

    validate_contract("run", run)
    assert run["status"] == "intake"
    assert run["current_gate"] == "data_contract"
    assert run["delivery_level"] == 0
    assert author_queue == {
        "author": {"display_name": "Dr. Who", "status": "placeholder"},
        "items": [
            {
                "field": "author_identity",
                "placeholder": "Dr. Who",
                "status": "pending",
            }
        ],
    }
    assert journal == {
        "journal_name": "生物多样性",
        "main_language": "zh-CN",
        "bilingual_elements": ["title", "abstract", "keywords"],
        "source_url": "https://www.biodiversity-science.net/CN/column/column49.shtml",
    }


def test_initialize_project_creates_directories_and_empty_logs(tmp_path: Path):
    project = initialize_project(tmp_path)

    assert project.root == tmp_path
    assert project.wmb_dir == tmp_path / ".wmb"
    for directory in (
        project.tasks_dir,
        project.artifacts_dir,
        project.reviews_dir,
        project.decisions_dir,
        project.logs_dir,
    ):
        assert directory.is_dir()
    assert project.events_log.read_text(encoding="utf-8") == ""
    assert project.rejections_log.read_text(encoding="utf-8") == ""


def test_initialize_project_is_idempotent_and_preserves_existing_records(
    tmp_path: Path,
):
    project = initialize_project(tmp_path)
    records = {
        project.run_file: (
            "run_id: existing\n"
            "status: blocked\n"
            "current_gate: author_confirmation\n"
            "delivery_level: 2\n"
        ),
        project.author_confirmation_queue_file: (
            "author:\n"
            "  display_name: Existing Author\n"
            "  status: confirmed\n"
            "items: []\n"
        ),
        project.journal_contract_file: (
            "journal_name: Existing Journal\n"
            "main_language: en-US\n"
            "bilingual_elements: []\n"
            "source_url: https://example.org/guidelines\n"
        ),
        project.events_log: (
            '{"event_id":"existing","timestamp":"2026-06-12T09:00:00Z",'
            '"actor":"orchestrator","event_type":"transition",'
            '"from_status":"intake","to_status":"blocked","reason":"existing"}\n'
        ),
        project.rejections_log: '{"record_id": "existing"}\n',
    }
    for path, content in records.items():
        path.write_text(content, encoding="utf-8")

    same_project = initialize_project(tmp_path)

    assert same_project == project
    for path, content in records.items():
        assert path.read_text(encoding="utf-8") == content


def test_initialize_project_uses_custom_author_and_journal(tmp_path: Path):
    author = {"display_name": "Ada Lovelace", "status": "confirmed"}
    journal = {
        "journal_name": "Journal of Wildlife Management",
        "main_language": "en-US",
        "bilingual_elements": [],
        "source_url": "https://example.org/author-guidelines",
    }

    project = initialize_project(tmp_path, author=author, journal=journal)

    author_queue = _load_yaml(project.author_confirmation_queue_file)
    assert author_queue == {"author": author, "items": []}
    assert _load_yaml(project.journal_contract_file) == journal


@pytest.mark.parametrize(
    "author",
    [
        "",
        "   ",
        {},
        {"display_name": "   ", "status": "confirmed"},
    ],
)
def test_missing_author_inputs_retain_pending_identity(tmp_path: Path, author):
    project = initialize_project(tmp_path, author=author)

    assert _load_yaml(project.author_confirmation_queue_file) == {
        "author": {"display_name": "Dr. Who", "status": "placeholder"},
        "items": [
            {
                "field": "author_identity",
                "placeholder": "Dr. Who",
                "status": "pending",
            }
        ],
    }


def test_incomplete_author_mapping_is_rejected(tmp_path: Path):
    with pytest.raises(ValueError, match="status"):
        initialize_project(tmp_path, author={"display_name": "Ada Lovelace"})


@pytest.mark.parametrize(
    ("content", "error"),
    [
        ("run_id: [unterminated", yaml.YAMLError),
        ("run_id: existing\nstatus: blocked\n", ContractError),
    ],
)
def test_initialize_project_rejects_invalid_existing_run_without_overwriting(
    tmp_path: Path,
    content: str,
    error: type[Exception],
):
    run_file = tmp_path / ".wmb" / "run.yaml"
    run_file.parent.mkdir()
    run_file.write_text(content, encoding="utf-8")

    with pytest.raises(error):
        initialize_project(tmp_path)

    assert run_file.read_text(encoding="utf-8") == content


def test_initialize_project_rejects_non_file_run_path(tmp_path: Path):
    run_file = tmp_path / ".wmb" / "run.yaml"
    run_file.mkdir(parents=True)

    with pytest.raises(IsADirectoryError):
        initialize_project(tmp_path)

    assert run_file.is_dir()


def test_project_root_is_normalized_to_stable_absolute_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.chdir(tmp_path)

    project = initialize_project(Path("nested") / ".." / "project")

    assert project.root == (tmp_path / "project").resolve()
    assert ProjectPaths(Path(".")).root == tmp_path.resolve()


def test_initialize_project_falls_back_when_hard_links_are_unsupported(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    def unsupported_link(*_args, **_kwargs):
        raise OSError(errno.ENOTSUP, "hard links unsupported")

    monkeypatch.setattr(project_module.os, "link", unsupported_link)

    project = initialize_project(tmp_path)
    original_run = project.run_file.read_text(encoding="utf-8")
    existing_event = (
        '{"event_id":"existing","timestamp":"2026-06-12T09:00:00Z",'
        '"actor":"orchestrator","event_type":"transition",'
        '"from_status":"intake","to_status":"blocked","reason":"existing"}\n'
    )
    project.events_log.write_text(existing_event, encoding="utf-8")

    initialize_project(tmp_path)

    validate_contract("run", _load_yaml(project.run_file))
    assert project.run_file.read_text(encoding="utf-8") == original_run
    assert project.events_log.read_text(encoding="utf-8") == existing_event


def test_initialize_project_does_not_require_hard_link_api(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.delattr(project_module.os, "link")

    project = initialize_project(tmp_path)

    validate_contract("run", _load_yaml(project.run_file))


def test_hard_link_fallback_is_atomic_under_concurrent_initialization(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    def unsupported_link(*_args, **_kwargs):
        raise OSError(errno.ENOTSUP, "hard links unsupported")

    monkeypatch.setattr(project_module.os, "link", unsupported_link)

    for attempt in range(10):
        root = tmp_path / str(attempt)
        with ThreadPoolExecutor(max_workers=8) as pool:
            projects = list(
                pool.map(lambda _: initialize_project(root), range(16))
            )

        validate_contract("run", _load_yaml(projects[0].run_file))


def test_hard_link_fallback_never_publishes_partial_run(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    def unsupported_link(*_args, **_kwargs):
        raise OSError(errno.ENOTSUP, "hard links unsupported")

    real_fdopen = project_module.os.fdopen
    write_started = Event()
    release_write = Event()

    class BlockingWriter:
        def __init__(self, destination):
            self.destination = destination

        def __enter__(self):
            self.destination.__enter__()
            return self

        def __exit__(self, *args):
            return self.destination.__exit__(*args)

        def write(self, content):
            write_started.set()
            release_write.wait(timeout=5)
            return self.destination.write(content)

        def flush(self):
            return self.destination.flush()

        def fileno(self):
            return self.destination.fileno()

    def blocking_fdopen(*args, **kwargs):
        return BlockingWriter(real_fdopen(*args, **kwargs))

    monkeypatch.setattr(project_module.os, "link", unsupported_link)
    monkeypatch.setattr(project_module.os, "fdopen", blocking_fdopen)

    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(initialize_project, tmp_path)
        if write_started.wait(timeout=0.2):
            second = pool.submit(initialize_project, tmp_path)
            try:
                second_error = second.exception(timeout=1)
            finally:
                release_write.set()
            first.result()
        else:
            first.result()
            second_error = pool.submit(
                initialize_project,
                tmp_path,
            ).exception(timeout=1)

    assert second_error is None


def test_fallback_exclusive_creation_preserves_concurrent_target(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    target = tmp_path / "record.yaml"
    real_open = project_module.os.open
    concurrent_content = "owner: concurrent\n"
    injected = False

    def race_open(path, flags, mode=0o777):
        nonlocal injected
        if Path(path) == target and flags & os.O_EXCL and not injected:
            injected = True
            target.write_text(concurrent_content, encoding="utf-8")
        return real_open(path, flags, mode)

    def unsupported_link(*_args, **_kwargs):
        raise OSError(errno.ENOTSUP, "hard links unsupported")

    monkeypatch.setattr(project_module.os, "link", unsupported_link)
    monkeypatch.setattr(project_module.os, "open", race_open)

    project_module._write_once(target, "owner: initializer\n")

    assert injected
    assert target.read_text(encoding="utf-8") == concurrent_content


def test_fallback_write_failure_does_not_delete_replacement_target(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    target = tmp_path / "record.yaml"
    concurrent_content = "owner: concurrent\n"
    real_write_descriptor = project_module._write_descriptor
    writes = 0

    def unsupported_link(*_args, **_kwargs):
        raise OSError(errno.ENOTSUP, "hard links unsupported")

    def replace_then_fail(descriptor, content):
        nonlocal writes
        writes += 1
        if writes == 1:
            return real_write_descriptor(descriptor, content)
        os.close(descriptor)
        target.unlink()
        target.write_text(concurrent_content, encoding="utf-8")
        raise OSError("simulated target write failure")

    monkeypatch.setattr(project_module.os, "link", unsupported_link)
    monkeypatch.setattr(project_module, "_write_descriptor", replace_then_fail)

    with pytest.raises(OSError, match="simulated target write failure"):
        project_module._write_once(target, "owner: initializer\n")

    assert target.read_text(encoding="utf-8") == concurrent_content


def test_stale_fallback_lock_is_recovered_after_crash(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    run_file = tmp_path / ".wmb" / "run.yaml"
    lock_file = project_module._publish_lock_path(run_file)
    lock_file.parent.mkdir(parents=True)
    lock_file.write_text('{"pid": 99999999, "created_at": 0}', encoding="utf-8")
    os.utime(lock_file, (0, 0))
    monkeypatch.setattr(project_module, "_PUBLISH_LOCK_STALE_SECONDS", 0.01)

    project = initialize_project(tmp_path)

    validate_contract("run", _load_yaml(project.run_file))
    assert not lock_file.exists()


def test_fresh_fallback_lock_without_target_is_not_stolen(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    run_file = tmp_path / ".wmb" / "run.yaml"
    lock_file = project_module._publish_lock_path(run_file)
    lock_file.parent.mkdir(parents=True)
    content = '{"pid": 1, "token": "active"}'
    lock_file.write_text(content, encoding="utf-8")
    monkeypatch.setattr(project_module, "_PUBLISH_LOCK_ATTEMPTS", 1)
    monkeypatch.setattr(project_module, "_PUBLISH_LOCK_STALE_SECONDS", 60.0)

    with pytest.raises(TimeoutError):
        initialize_project(tmp_path)

    assert lock_file.read_text(encoding="utf-8") == content


def test_completed_target_recovers_leftover_fallback_lock(tmp_path: Path):
    project = initialize_project(tmp_path)
    original = project.run_file.read_text(encoding="utf-8")
    lock_file = project_module._publish_lock_path(project.run_file)
    lock_file.write_text('{"pid": 99999999}', encoding="utf-8")

    initialize_project(tmp_path)

    assert project.run_file.read_text(encoding="utf-8") == original
    assert not lock_file.exists()


@pytest.mark.parametrize(
    "relative_path",
    [
        "author_confirmation_queue.yaml",
        "journal_contract.yaml",
        "logs/events.jsonl",
        "logs/rejections.jsonl",
    ],
)
def test_initialize_project_rejects_non_file_record_paths(
    tmp_path: Path,
    relative_path: str,
):
    record_path = tmp_path / ".wmb" / relative_path
    record_path.mkdir(parents=True)

    with pytest.raises(IsADirectoryError):
        initialize_project(tmp_path)

    assert record_path.is_dir()


def test_initialize_project_rejects_non_directory_logs_path(tmp_path: Path):
    logs_path = tmp_path / ".wmb" / "logs"
    logs_path.parent.mkdir()
    logs_path.write_text("not a directory", encoding="utf-8")

    with pytest.raises(NotADirectoryError):
        initialize_project(tmp_path)

    assert logs_path.read_text(encoding="utf-8") == "not a directory"


@pytest.mark.parametrize(
    ("relative_path", "content", "error"),
    [
        ("author_confirmation_queue.yaml", "items: []\n", ValueError),
        ("journal_contract.yaml", "journal_name: Existing Journal\n", ValueError),
        ("logs/events.jsonl", '{"event_id":"existing"}\n', ContractError),
        ("logs/rejections.jsonl", "[]\n", ValueError),
    ],
)
def test_initialize_project_rejects_unusable_existing_records_without_overwrite(
    tmp_path: Path,
    relative_path: str,
    content: str,
    error: type[Exception],
):
    project = initialize_project(tmp_path)
    record_path = project.wmb_dir / relative_path
    record_path.write_text(content, encoding="utf-8")

    with pytest.raises(error):
        initialize_project(tmp_path)

    assert record_path.read_text(encoding="utf-8") == content


@pytest.mark.parametrize("journal", ["", "   ", {}, {"journal_name": "   "}])
def test_blank_journal_inputs_use_default_contract(tmp_path: Path, journal):
    project = initialize_project(tmp_path, journal=journal)

    assert _load_yaml(project.journal_contract_file) == {
        "journal_name": "生物多样性",
        "main_language": "zh-CN",
        "bilingual_elements": ["title", "abstract", "keywords"],
        "source_url": "https://www.biodiversity-science.net/CN/column/column49.shtml",
    }


@pytest.mark.parametrize(
    "journal",
    [
        "Journal of Wildlife Management",
        {"journal_name": "Journal of Wildlife Management"},
    ],
)
def test_incomplete_journal_contract_is_rejected(tmp_path: Path, journal):
    with pytest.raises(ValueError, match="journal"):
        initialize_project(tmp_path, journal=journal)

    assert not (tmp_path / ".wmb" / "journal_contract.yaml").exists()


@pytest.mark.parametrize(
    ("relative_path", "final_validation_call"),
    [
        ("run.yaml", 3),
        ("author_confirmation_queue.yaml", 2),
        ("journal_contract.yaml", 2),
        ("logs/events.jsonl", 2),
        ("logs/rejections.jsonl", 2),
    ],
)
def test_final_validation_rejects_concurrently_removed_canonical_record(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    relative_path: str,
    final_validation_call: int,
):
    target = tmp_path / ".wmb" / relative_path
    real_validate = project_module._validate_existing_record
    calls = 0

    def remove_before_final_validation(path, validator):
        nonlocal calls
        if path == target:
            calls += 1
            if calls == final_validation_call:
                path.unlink()
        return real_validate(path, validator)

    monkeypatch.setattr(
        project_module,
        "_validate_existing_record",
        remove_before_final_validation,
    )

    with pytest.raises(InitializationError, match=target.name):
        initialize_project(tmp_path)


def test_final_validation_wraps_concurrent_record_corruption(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    target = tmp_path / ".wmb" / "journal_contract.yaml"
    real_validate = project_module._validate_existing_record
    calls = 0

    def corrupt_before_final_validation(path, validator):
        nonlocal calls
        if path == target:
            calls += 1
            if calls == 2:
                path.write_text("journal_name: broken\n", encoding="utf-8")
        return real_validate(path, validator)

    monkeypatch.setattr(
        project_module,
        "_validate_existing_record",
        corrupt_before_final_validation,
    )

    with pytest.raises(InitializationError, match="journal_contract.yaml"):
        initialize_project(tmp_path)


def test_final_validation_detects_record_removed_after_it_passes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    run_file = tmp_path / ".wmb" / "run.yaml"
    last_record = tmp_path / ".wmb" / "logs" / "rejections.jsonl"
    real_validate = project_module._validate_existing_record
    last_record_calls = 0

    def remove_previous_record_during_final_validation(path, validator):
        nonlocal last_record_calls
        if path == last_record:
            last_record_calls += 1
            if last_record_calls == 2:
                run_file.unlink()
        return real_validate(path, validator)

    monkeypatch.setattr(
        project_module,
        "_validate_existing_record",
        remove_previous_record_during_final_validation,
    )

    with pytest.raises(InitializationError, match="run.yaml"):
        initialize_project(tmp_path)
