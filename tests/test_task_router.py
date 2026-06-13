from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from wmb.contracts import ContractError, validate_contract
from wmb.core.project import initialize_project
from wmb.core.task_router import TaskRouter


def _load_yaml(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_router_selects_all_applicable_ecology_capabilities_deterministically(
    tmp_path: Path,
):
    router = TaskRouter(initialize_project(tmp_path))

    capabilities = router.select_capabilities(
        data_types=["camera_trap", "acoustic_monitoring", "remote_sensing"],
        methods=["occupancy", "activity_curves", "sdm"],
        risks=["sensitive_location"],
        stage="evidence_and_analysis",
    )

    assert capabilities == sorted(capabilities)
    assert {
        "activity_pattern_statistician",
        "acoustic_ecologist",
        "analysis_reviewer",
        "camera_trap_ecologist",
        "occupancy_statistician",
        "remote_sensing_ecologist",
        "sensitive_location_reviewer",
        "spatial_modeler",
    }.issubset(capabilities)


def test_router_accepts_existing_wmb_grouped_type_and_method_labels(tmp_path: Path):
    router = TaskRouter(initialize_project(tmp_path))

    capabilities = router.select_capabilities(
        data_types=[
            "Transect, Point Count, and Direct Survey",
            "Occupancy, Distribution, and Habitat Suitability",
        ],
        methods=["spatial GLM/GLMM", "REM/REST", "time/space-to-event"],
        risks=[],
        stage="evidence_and_analysis",
    )

    assert {
        "abundance_statistician",
        "occupancy_ecologist",
        "spatial_modeler",
        "survey_ecologist",
    }.issubset(capabilities)


@pytest.mark.parametrize(
    ("stage", "expected"),
    [
        ("awaiting_research_direction", "research_direction_reviewer"),
        ("manuscript_drafting", "manuscript_writer"),
        ("independent_review", "independent_reviewer"),
        ("package_verification", "package_reviewer"),
    ],
)
def test_router_adds_generic_capability_for_stage(
    tmp_path: Path,
    stage: str,
    expected: str,
):
    router = TaskRouter(initialize_project(tmp_path))

    assert expected in router.select_capabilities([], [], [], stage)


def test_create_task_emits_valid_contract_and_persists_it(tmp_path: Path):
    project = initialize_project(tmp_path)
    router = TaskRouter(project)

    task = router.create_task(
        "occupancy_statistician",
        "Fit occupancy models",
        ["data/camera_trap.csv"],
        [".wmb/artifacts/occupancy_result.yaml"],
        acceptance_criteria=["report uncertainty"],
        prohibited_actions=["change response variable"],
        max_attempts=2,
    )

    validate_contract("task", task)
    assert task["role"] == "worker"
    assert task["context_id"].startswith("context-")
    assert task["status"] == "pending"
    assert _load_yaml(project.tasks_dir / f"{task['task_id']}.yaml") == task


@pytest.mark.parametrize(
    "changes",
    [
        {"role": "orchestrator"},
        {"context_id": ""},
        {"role": "reviewer"},
        {"role": "worker", "review_of": "task-other"},
    ],
)
def test_task_contract_validates_isolation_metadata(tmp_path: Path, changes: dict):
    task = TaskRouter(initialize_project(tmp_path)).create_task(
        "manuscript_writer",
        "Draft",
        [],
        ["draft.md"],
    )
    invalid = {**task, **changes}

    with pytest.raises(ContractError):
        validate_contract("task", invalid)


def test_reviewer_uses_isolated_context_and_only_reviewed_worker_outputs(
    tmp_path: Path,
):
    router = TaskRouter(initialize_project(tmp_path))
    worker = router.create_task(
        "manuscript_writer",
        "Draft Results",
        [],
        ["draft.md"],
    )

    reviewer = router.create_task(
        "statistical_reviewer",
        "Review Results",
        ["draft.md"],
        ["review.yaml"],
        review_of=worker["task_id"],
    )

    assert reviewer["role"] == "reviewer"
    assert reviewer["review_of"] == worker["task_id"]
    assert reviewer["context_id"] != worker["context_id"]


def test_reviewer_rejects_explicitly_shared_worker_context(tmp_path: Path):
    router = TaskRouter(initialize_project(tmp_path))
    worker = router.create_task("manuscript_writer", "Draft", [], ["draft.md"])

    with pytest.raises(ValueError, match="context"):
        router.create_task(
            "statistical_reviewer",
            "Review",
            ["draft.md"],
            ["review.yaml"],
            review_of=worker["task_id"],
            context_id=worker["context_id"],
        )


def test_reviewer_requires_existing_worker_task(tmp_path: Path):
    router = TaskRouter(initialize_project(tmp_path))

    with pytest.raises(ValueError, match="existing worker task"):
        router.create_task(
            "statistical_reviewer",
            "Review",
            [],
            ["review.yaml"],
            review_of="task-missing",
        )

    worker = router.create_task("manuscript_writer", "Draft", [], ["draft.md"])
    reviewer = router.create_task(
        "statistical_reviewer",
        "Review",
        ["draft.md"],
        ["review.yaml"],
        review_of=worker["task_id"],
    )

    with pytest.raises(ValueError, match="existing worker task"):
        router.create_task(
            "citation_reviewer",
            "Review the review",
            ["review.yaml"],
            ["second-review.yaml"],
            review_of=reviewer["task_id"],
        )


def test_reviewer_rejects_worker_file_with_mismatched_task_id(tmp_path: Path):
    project = initialize_project(tmp_path)
    router = TaskRouter(project)
    worker = router.create_task("manuscript_writer", "Draft", [], ["draft.md"])
    worker_path = project.tasks_dir / f"{worker['task_id']}.yaml"
    tampered = {**worker, "task_id": "task-other"}
    worker_path.write_text(
        yaml.safe_dump(tampered, sort_keys=False),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="existing worker task"):
        router.create_task(
            "statistical_reviewer",
            "Review",
            ["draft.md"],
            ["review.yaml"],
            review_of=worker["task_id"],
        )


def test_reviewer_rejects_inputs_not_emitted_by_reviewed_worker(tmp_path: Path):
    router = TaskRouter(initialize_project(tmp_path))
    worker = router.create_task("manuscript_writer", "Draft", [], ["draft.md"])

    with pytest.raises(ValueError, match="unlisted"):
        router.create_task(
            "statistical_reviewer",
            "Review",
            ["draft.md", "unlisted-analysis.csv"],
            ["review.yaml"],
            review_of=worker["task_id"],
        )


@pytest.mark.parametrize("capability", ["manuscript_writer", "statistical_reviewer"])
def test_general_capabilities_cannot_access_sensitive_inputs(
    tmp_path: Path,
    capability: str,
):
    router = TaskRouter(initialize_project(tmp_path))
    review_of = None
    required_outputs = ["draft.md"]
    if capability.endswith("_reviewer"):
        worker = router.create_task(
            "sensitive_data_analyst",
            "Prepare restricted result",
            [],
            [".wmb/artifacts/sensitive/exact_locations.csv"],
        )
        review_of = worker["task_id"]
        required_outputs = ["review.yaml"]

    with pytest.raises(ValueError, match="restricted"):
        router.create_task(
            capability,
            "Use sensitive locations",
            [".wmb/artifacts/sensitive/exact_locations.csv"],
            required_outputs,
            review_of=review_of,
        )


def test_sensitive_location_reviewer_can_access_listed_sensitive_worker_output(
    tmp_path: Path,
):
    router = TaskRouter(initialize_project(tmp_path))
    sensitive_output = ".wmb/artifacts/sensitive/exact_locations.csv"
    worker = router.create_task(
        "sensitive_data_analyst",
        "Prepare restricted result",
        [],
        [sensitive_output],
    )

    reviewer = router.create_task(
        "sensitive_location_reviewer",
        "Check disclosure risk",
        [sensitive_output],
        ["sensitive-review.yaml"],
        review_of=worker["task_id"],
    )

    assert reviewer["allowed_inputs"] == [sensitive_output]


def test_task_id_collision_never_overwrites_existing_task(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    project = initialize_project(tmp_path)
    collision_path = project.tasks_dir / "task-collision.yaml"
    original = "owner: existing\n"
    collision_path.write_text(original, encoding="utf-8")
    identifiers = iter(
        [
            SimpleNamespace(hex="context"),
            SimpleNamespace(hex="collision"),
            SimpleNamespace(hex="unique"),
        ]
    )
    monkeypatch.setattr(
        "wmb.core.task_router.uuid4",
        lambda: next(identifiers),
    )

    task = TaskRouter(project).create_task(
        "manuscript_writer",
        "Draft",
        [],
        ["draft.md"],
    )

    assert task["task_id"] == "task-unique"
    assert collision_path.read_text(encoding="utf-8") == original
    assert (project.tasks_dir / "task-unique.yaml").is_file()
