from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace
from threading import Barrier, Event, Lock

import pytest
import yaml

from wmb.contracts import ContractError, validate_contract
from wmb.core import task_router as task_router_module
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


def test_router_surfaces_unknown_methods_and_risks_without_dropping_them(
    tmp_path: Path,
):
    selection = TaskRouter(initialize_project(tmp_path)).select_capabilities(
        data_types=[],
        methods=["novel Bayesian fox model"],
        risks=["community consent"],
        stage="evidence_and_analysis",
        target_journal="Journal of Wildlife Management",
    )

    assert "generic_method_specialist" in selection
    assert "generic_risk_reviewer" in selection
    assert "journal_requirements_reviewer" in selection
    assert selection.warnings == (
        "unknown method: novel Bayesian fox model",
        "unknown risk: community consent",
    )
    assert selection.routing_warnings == selection.warnings


def test_router_routes_existing_population_method_families(tmp_path: Path):
    selection = TaskRouter(initialize_project(tmp_path)).select_capabilities(
        data_types=["population_ecology"],
        methods=[
            "CJS",
            "POPAN",
            "robust design",
            "multi-state",
            "capture-recapture",
            "matrix models",
        ],
        risks=[],
        stage="evidence_and_analysis",
    )

    assert "population_ecologist" in selection
    assert "population_statistician" in selection
    assert selection.warnings == ()


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
        ("intake", {"data_contract_reviewer"}),
        (
            "awaiting_research_direction",
            {"research_direction_reviewer", "research_direction_writer"},
        ),
        ("evidence_and_analysis", {"analysis_reviewer"}),
        ("result_and_claim_build", {"claim_reviewer", "result_card_writer"}),
        ("manuscript_drafting", {"manuscript_writer"}),
        ("independent_review", {"independent_reviewer", "statistical_reviewer"}),
        ("package_verification", {"package_reviewer", "statistical_reviewer"}),
        (
            "awaiting_final_confirmation",
            {"final_package_reviewer", "statistical_reviewer"},
        ),
        ("candidate_level_4", {"package_reviewer", "statistical_reviewer"}),
        ("downgraded", {"deliverable_writer"}),
        ("blocked", {"blocker_reviewer"}),
    ],
)
def test_router_adds_generic_capability_for_stage(
    tmp_path: Path,
    stage: str,
    expected: set[str],
):
    router = TaskRouter(initialize_project(tmp_path))

    assert expected.issubset(router.select_capabilities([], [], [], stage))


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
        {"capability": "statistical_reviewer", "role": "worker"},
        {
            "capability": "manuscript_writer",
            "role": "reviewer",
            "review_of": "task-other",
        },
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


def test_task_contract_requires_role_and_context_id(tmp_path: Path):
    task = TaskRouter(initialize_project(tmp_path)).create_task(
        "manuscript_writer",
        "Draft",
        [],
        ["draft.md"],
    )

    for field in ("role", "context_id"):
        invalid = {**task}
        del invalid[field]
        with pytest.raises(ContractError, match=field):
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


@pytest.mark.parametrize("reuse_role", ["worker", "reviewer"])
def test_reviewer_rejects_context_reused_from_any_existing_task(
    tmp_path: Path,
    reuse_role: str,
):
    router = TaskRouter(initialize_project(tmp_path))
    reviewed_worker = router.create_task(
        "manuscript_writer",
        "Draft reviewed artifact",
        [],
        ["reviewed.md"],
    )
    unrelated_worker = router.create_task(
        "manuscript_writer",
        "Draft unrelated artifact",
        [],
        ["unrelated.md"],
    )
    existing = unrelated_worker
    if reuse_role == "reviewer":
        existing = router.create_task(
            "statistical_reviewer",
            "Review unrelated artifact",
            ["unrelated.md"],
            ["unrelated-review.yaml"],
            review_of=unrelated_worker["task_id"],
        )

    with pytest.raises(ValueError, match="existing task context"):
        router.create_task(
            "statistical_reviewer",
            "Review reviewed artifact",
            ["reviewed.md"],
            ["review.yaml"],
            review_of=reviewed_worker["task_id"],
            context_id=existing["context_id"],
        )


def test_reviewer_ignores_new_supplied_context_and_generates_its_own(tmp_path: Path):
    router = TaskRouter(initialize_project(tmp_path))
    worker = router.create_task("manuscript_writer", "Draft", [], ["draft.md"])

    reviewer = router.create_task(
        "statistical_reviewer",
        "Review",
        ["draft.md"],
        ["review.yaml"],
        review_of=worker["task_id"],
        context_id="context-caller-supplied",
    )

    assert reviewer["context_id"] != "context-caller-supplied"


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


def test_reviewer_accepts_worker_outputs_and_registered_review_materials(
    tmp_path: Path,
):
    router = TaskRouter(initialize_project(tmp_path))
    router.register_artifact("verified-analysis.yaml", "verified_analysis")
    router.register_artifact("review-criteria.md", "review_criteria")
    worker = router.create_task("manuscript_writer", "Draft", [], ["draft.md"])

    reviewer = router.create_task(
        "statistical_reviewer",
        "Review",
        ["draft.md", "verified-analysis.yaml", "review-criteria.md"],
        ["review.yaml"],
        review_of=worker["task_id"],
    )

    assert reviewer["allowed_inputs"] == [
        "draft.md",
        "verified-analysis.yaml",
        "review-criteria.md",
    ]


def test_reviewer_rejects_unauthorized_inputs(tmp_path: Path):
    router = TaskRouter(initialize_project(tmp_path))
    worker = router.create_task("manuscript_writer", "Draft", [], ["draft.md"])

    with pytest.raises(ValueError, match="unauthorized"):
        router.create_task(
            "statistical_reviewer",
            "Review",
            ["draft.md", "unlisted-analysis.csv"],
            ["review.yaml"],
            review_of=worker["task_id"],
        )


def test_artifact_manifest_authoritatively_restricts_arbitrary_filename(
    tmp_path: Path,
):
    project = initialize_project(tmp_path)
    router = TaskRouter(project)
    router.classify_artifact("ordinary-looking.bin", "restricted")

    with pytest.raises(ValueError, match="restricted"):
        router.create_task(
            "manuscript_writer",
            "Draft",
            ["ordinary-looking.bin"],
            ["draft.md"],
        )

    manifest = _load_yaml(project.artifacts_dir / "manifest.yaml")
    assert manifest["artifacts"]["ordinary-looking.bin"]["classification"] == (
        "restricted"
    )


def test_concurrent_router_instances_merge_artifact_manifest_updates(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    project = initialize_project(tmp_path)
    first_router = TaskRouter(project)
    second_router = TaskRouter(project)
    first_write_started = Event()
    release_first_write = Event()
    second_loaded = Event()
    real_atomic_write = task_router_module._atomic_write_text
    real_second_load = second_router._load_artifact_manifest
    write_lock = Lock()
    writes = 0

    def blocking_first_write(path, content):
        nonlocal writes
        with write_lock:
            writes += 1
            write_number = writes
        if write_number == 1:
            first_write_started.set()
            release_first_write.wait(timeout=5)
        return real_atomic_write(path, content)

    def observe_second_load():
        second_loaded.set()
        return real_second_load()

    monkeypatch.setattr(task_router_module, "_atomic_write_text", blocking_first_write)
    monkeypatch.setattr(second_router, "_load_artifact_manifest", observe_second_load)

    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(first_router.register_artifact, "first.bin", "verified")
        assert first_write_started.wait(timeout=5)
        second = pool.submit(
            second_router.register_artifact,
            "second.bin",
            "review_criteria",
        )
        if second_loaded.wait(timeout=0.1):
            second.result(timeout=5)
        release_first_write.set()
        first.result(timeout=5)
        second.result(timeout=5)

    manifest = _load_yaml(project.artifacts_dir / "manifest.yaml")
    assert set(manifest["artifacts"]) == {"first.bin", "second.bin"}


def test_concurrent_artifact_classification_conflict_keeps_restricted(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    project = initialize_project(tmp_path)
    first_router = TaskRouter(project)
    second_router = TaskRouter(project)
    artifact_id = "ordinary.bin"
    restricted_written = Event()
    release_restricted_writer = Event()
    real_atomic_write = task_router_module._atomic_write_text
    write_lock = Lock()
    writes = 0

    def hold_lock_after_restricted_write(path, content):
        nonlocal writes
        with write_lock:
            writes += 1
            write_number = writes
        real_atomic_write(path, content)
        if write_number == 1:
            restricted_written.set()
            release_restricted_writer.wait(timeout=5)

    monkeypatch.setattr(
        task_router_module,
        "_atomic_write_text",
        hold_lock_after_restricted_write,
    )

    with ThreadPoolExecutor(max_workers=2) as pool:
        restricted = pool.submit(
            first_router.register_artifact,
            artifact_id,
            "restricted",
        )
        assert restricted_written.wait(timeout=5)
        verified = pool.submit(
            second_router.register_artifact,
            artifact_id,
            "verified",
        )
        release_restricted_writer.set()
        restricted.result(timeout=5)
        verified.result(timeout=5)

    manifest = _load_yaml(project.artifacts_dir / "manifest.yaml")
    assert manifest["artifacts"][artifact_id]["classification"] == "restricted"


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


def test_concurrent_same_content_tasks_get_distinct_task_ids(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    router = TaskRouter(initialize_project(tmp_path))
    first_calls = Barrier(2)
    counter_lock = Lock()
    calls = 0

    def colliding_uuid():
        nonlocal calls
        with counter_lock:
            calls += 1
            call = calls
        if call <= 2:
            first_calls.wait(timeout=5)
            return SimpleNamespace(hex="collision")
        return SimpleNamespace(hex=f"unique-{call}")

    monkeypatch.setattr("wmb.core.task_router.uuid4", colliding_uuid)

    def create():
        return router.create_task(
            "manuscript_writer",
            "Draft",
            [],
            ["draft.md"],
            context_id="context-shared-worker",
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        tasks = list(pool.map(lambda _: create(), range(2)))

    assert len({task["task_id"] for task in tasks}) == 2
