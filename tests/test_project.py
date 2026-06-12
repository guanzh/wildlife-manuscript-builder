from pathlib import Path

import yaml

from wmb.contracts import validate_contract
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
        project.run_file: "run_id: existing\nstatus: blocked\n",
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
