import errno
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Event

import pytest
import yaml

from wmb.contracts import ContractError, validate_contract
from wmb.core import project as project_module
from wmb.core.models import ProjectPaths
from wmb.core.project import initialize_project


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
        project.author_confirmation_queue_file: "items:\n  - existing: author\n",
        project.journal_contract_file: "journal_name: Existing Journal\n",
        project.events_log: '{"event_id": "existing"}\n',
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
    project.events_log.write_text("existing event\n", encoding="utf-8")

    initialize_project(tmp_path)

    validate_contract("run", _load_yaml(project.run_file))
    assert project.run_file.read_text(encoding="utf-8") == original_run
    assert project.events_log.read_text(encoding="utf-8") == "existing event\n"


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
