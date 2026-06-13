import os
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from pathlib import Path
from types import SimpleNamespace
from threading import Event, Lock

import pytest
import yaml

from wmb.contracts import ContractError, validate_contract
from wmb.core import task_router as task_router_module
from wmb.core.project import initialize_project
from wmb.core.task_router import TaskRouter


def _load_yaml(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _set_task_status(project, task: dict, status: str) -> dict:
    updated = {**task, "status": status}
    if status == "revoked":
        updated["revocation_reason"] = "test revocation"
    path = project.tasks_dir / f"{task['task_id']}.yaml"
    path.write_text(yaml.safe_dump(updated, sort_keys=False), encoding="utf-8")
    return updated


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


@pytest.mark.parametrize("field", ["data_types", "methods"])
def test_router_routes_mark_recapture_alias_to_population_modeler(
    tmp_path: Path,
    field: str,
):
    arguments = {"data_types": [], "methods": []}
    arguments[field] = ["mark-recapture"]

    selection = TaskRouter(initialize_project(tmp_path)).select_capabilities(
        **arguments,
        risks=[],
        stage="evidence_and_analysis",
    )

    assert "population_modeler" in selection


def test_router_routes_exact_molecular_ecology_grouped_alias(tmp_path: Path):
    selection = TaskRouter(initialize_project(tmp_path)).select_capabilities(
        data_types=["Molecular Ecology (eDNA, Metabarcoding)"],
        methods=[],
        risks=[],
        stage="evidence_and_analysis",
    )

    assert "molecular_ecologist" in selection
    assert "generic_ecology_specialist" not in selection
    assert selection.warnings == ()


def test_router_routes_exact_multivariate_community_models_alias(tmp_path: Path):
    selection = TaskRouter(initialize_project(tmp_path)).select_capabilities(
        data_types=[],
        methods=["multivariate community models"],
        risks=[],
        stage="evidence_and_analysis",
    )

    assert "community_modeler" in selection
    assert "generic_method_specialist" not in selection
    assert selection.warnings == ()


@pytest.mark.parametrize(
    ("method", "expected"),
    [
        ("landscape metrics", "landscape_modeler"),
        ("before-after with effort control", "intervention_statistician"),
        ("temporal/spatial overlap", "activity_pattern_statistician"),
        ("matched controls", "intervention_statistician"),
        ("multi-indicator framework", "integrated_modeler"),
        ("community indicators", "community_modeler"),
        ("GLM/GLMM", "ecological_statistician"),
        ("integrated occupancy or abundance", "integrated_modeler"),
        ("community classification and ordination", "community_modeler"),
        ("CJS, POPAN, robust design", "population_statistician"),
        ("matrix models, IPM, PVA", "population_statistician"),
        (
            "connectivity modeling (circuit theory, least-cost path, graph theory)",
            "landscape_modeler",
        ),
        ("BACI design", "intervention_statistician"),
        ("activity pattern analysis", "activity_pattern_statistician"),
    ],
)
def test_router_routes_documented_question_method_labels(
    tmp_path: Path,
    method: str,
    expected: str,
):
    selection = TaskRouter(initialize_project(tmp_path)).select_capabilities(
        data_types=[],
        methods=[method],
        risks=[],
        stage="evidence_and_analysis",
    )

    assert expected in selection
    assert "generic_method_specialist" not in selection
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
    ("stage", "expected_capability"),
    [
        ("novel analysis stage", "generic_stage_specialist"),
        ("novel peer review", "generic_stage_reviewer"),
        ("novel package verification", "generic_stage_reviewer"),
    ],
)
def test_router_surfaces_unknown_stage_with_generic_capability(
    tmp_path: Path,
    stage: str,
    expected_capability: str,
):
    selection = TaskRouter(initialize_project(tmp_path)).select_capabilities(
        data_types=[],
        methods=[],
        risks=[],
        stage=stage,
    )

    assert expected_capability in selection
    assert selection.warnings == (f"unknown stage: {stage}",)


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


def test_create_task_canonicalizes_capability_case_before_reviewer_policy(
    tmp_path: Path,
):
    project = initialize_project(tmp_path)
    router = TaskRouter(project)
    worker = router.create_task("manuscript_writer", "Draft", [], ["draft.md"])
    _set_task_status(project, worker, "completed")

    reviewer = router.create_task(
        "Statistical_Reviewer",
        "Review",
        ["draft.md"],
        ["review.yaml"],
        review_of=worker["task_id"],
    )

    assert reviewer["capability"] == "statistical_reviewer"
    assert reviewer["role"] == "reviewer"


@pytest.mark.parametrize(
    "capability",
    [
        "statistical-reviewer",
        "statistical reviewer",
        "statistical_reviewer/../manuscript_writer",
    ],
)
def test_create_task_rejects_unsafe_capability_strings(
    tmp_path: Path,
    capability: str,
):
    with pytest.raises(ValueError, match="capability"):
        TaskRouter(initialize_project(tmp_path)).create_task(
            capability,
            "Draft",
            [],
            ["draft.md"],
        )


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
    project = initialize_project(tmp_path)
    router = TaskRouter(project)
    worker = router.create_task(
        "manuscript_writer",
        "Draft Results",
        [],
        ["draft.md"],
    )
    _set_task_status(project, worker, "completed")

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
        _set_task_status(router.project, unrelated_worker, "completed")
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
    project = initialize_project(tmp_path)
    router = TaskRouter(project)
    worker = router.create_task("manuscript_writer", "Draft", [], ["draft.md"])
    _set_task_status(project, worker, "completed")

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
    project = initialize_project(tmp_path)
    router = TaskRouter(project)

    with pytest.raises(ValueError, match="existing worker task"):
        router.create_task(
            "statistical_reviewer",
            "Review",
            [],
            ["review.yaml"],
            review_of="task-missing",
        )

    worker = router.create_task("manuscript_writer", "Draft", [], ["draft.md"])
    _set_task_status(project, worker, "completed")
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


@pytest.mark.parametrize(
    "status",
    ["pending", "running", "failed", "revoked", "blocked", "cancelled"],
)
def test_reviewer_requires_completed_worker_status(tmp_path: Path, status: str):
    project = initialize_project(tmp_path)
    router = TaskRouter(project)
    worker = router.create_task("manuscript_writer", "Draft", [], ["draft.md"])
    _set_task_status(project, worker, status)

    with pytest.raises(ValueError, match="worker task|task context"):
        router.create_task(
            "statistical_reviewer",
            "Review",
            ["draft.md"],
            ["review.yaml"],
            review_of=worker["task_id"],
        )


def test_reviewer_rejects_restricted_derived_worker_outputs(tmp_path: Path):
    project = initialize_project(tmp_path)
    router = TaskRouter(project)
    output = "ordinary-analysis.bin"
    worker = router.create_task(
        "sensitive_data_analyst",
        "Analyze restricted source",
        [],
        [output],
    )
    _set_task_status(project, worker, "completed")
    router.classify_artifact(output, "restricted")

    with pytest.raises(ValueError, match="restricted-derived"):
        router.create_task(
            "sensitive_location_reviewer",
            "Review",
            [output],
            ["review.yaml"],
            review_of=worker["task_id"],
        )


def test_reviewer_rejects_outputs_derived_from_restricted_worker_inputs(
    tmp_path: Path,
):
    project = initialize_project(tmp_path)
    router = TaskRouter(project)
    source = "restricted-source.bin"
    output = "ordinary-analysis.bin"
    router.classify_artifact(source, "restricted")
    worker = router.create_task(
        "sensitive_data_analyst",
        "Analyze restricted source",
        [source],
        [output],
    )
    _set_task_status(project, worker, "completed")

    with pytest.raises(ValueError, match="restricted-derived"):
        router.create_task(
            "statistical_reviewer",
            "Review",
            [output],
            ["review.yaml"],
            review_of=worker["task_id"],
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
    project = initialize_project(tmp_path)
    router = TaskRouter(project)
    router.register_artifact("verified-analysis.yaml", "verified_analysis")
    router.register_artifact("review-criteria.md", "review_criteria")
    worker = router.create_task("manuscript_writer", "Draft", [], ["draft.md"])
    _set_task_status(project, worker, "completed")

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
    project = initialize_project(tmp_path)
    router = TaskRouter(project)
    worker = router.create_task("manuscript_writer", "Draft", [], ["draft.md"])
    _set_task_status(project, worker, "completed")

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


def test_artifact_alias_cannot_bypass_restricted_classification(tmp_path: Path):
    project = initialize_project(tmp_path)
    router = TaskRouter(project)
    router.classify_artifact("data/./Observations.csv", "restricted")
    alias = "DATA\\observations.csv" if os.name == "nt" else "data/Observations.csv"
    router.classify_artifact(alias, "verified")

    with pytest.raises(ValueError, match="restricted"):
        router.create_task(
            "manuscript_writer",
            "Draft",
            [alias],
            ["draft.md"],
        )

    manifest = _load_yaml(project.artifacts_dir / "manifest.yaml")
    expected = os.path.normcase("data/Observations.csv").replace("\\", "/")
    assert set(manifest["artifacts"]) == {expected}
    assert manifest["artifacts"][expected]["classification"] == "restricted"


def test_task_persists_canonical_artifact_ids(tmp_path: Path):
    task = TaskRouter(initialize_project(tmp_path)).create_task(
        "manuscript_writer",
        "Draft",
        ["data/./camera.csv"],
        ["drafts/./draft.md"],
    )

    assert task["allowed_inputs"] == [
        os.path.normcase("data/camera.csv").replace("\\", "/")
    ]
    assert task["required_outputs"] == [
        os.path.normcase("drafts/draft.md").replace("\\", "/")
    ]


def test_reviewer_authorization_compares_canonical_artifact_ids(tmp_path: Path):
    project = initialize_project(tmp_path)
    router = TaskRouter(project)
    worker = router.create_task(
        "manuscript_writer",
        "Draft",
        [],
        ["drafts/./draft.md"],
    )
    _set_task_status(project, worker, "completed")
    alias = "DRAFTS\\draft.md" if os.name == "nt" else "drafts/draft.md"

    reviewer = router.create_task(
        "statistical_reviewer",
        "Review",
        [alias],
        ["review.yaml"],
        review_of=worker["task_id"],
    )

    assert reviewer["allowed_inputs"] == [
        os.path.normcase("drafts/draft.md").replace("\\", "/")
    ]


def test_router_rejects_traversal_and_outside_project_artifact_ids(tmp_path: Path):
    router = TaskRouter(initialize_project(tmp_path))
    invalid_ids = [
        "../outside.csv",
        "data/../outside.csv",
        str(tmp_path.parent / "outside.csv"),
    ]

    for artifact_id in invalid_ids:
        with pytest.raises(ValueError, match="artifact"):
            router.classify_artifact(artifact_id, "restricted")
        with pytest.raises(ValueError, match="allowed_inputs"):
            router.create_task(
                "manuscript_writer",
                "Draft",
                [artifact_id],
                ["draft.md"],
            )
        with pytest.raises(ValueError, match="required_outputs"):
            router.create_task(
                "manuscript_writer",
                "Draft",
                [],
                [artifact_id],
            )


@pytest.mark.skipif(os.name != "nt", reason="Windows path alias rules")
@pytest.mark.parametrize(
    "artifact_id",
    [
        "data/report.csv.",
        "data/report.csv ",
        "data/CON",
        "data/con.txt",
        "data/CON .txt",
        "data/NUL.csv",
        "data/AUX/sub.csv",
        "data/COM1.txt",
        "data/LPT9",
        "data/bad?.csv",
    ],
)
def test_windows_artifact_aliases_are_rejected(
    tmp_path: Path,
    artifact_id: str,
):
    router = TaskRouter(initialize_project(tmp_path))

    with pytest.raises(ValueError, match="artifact"):
        router.classify_artifact(artifact_id, "restricted")
    with pytest.raises(ValueError, match="allowed_inputs"):
        router.create_task("manuscript_writer", "Draft", [artifact_id], ["draft.md"])


def test_general_capability_cannot_write_restricted_output(tmp_path: Path):
    router = TaskRouter(initialize_project(tmp_path))
    router.classify_artifact("ordinary-output.bin", "restricted")

    with pytest.raises(ValueError, match="restricted outputs"):
        router.create_task(
            "manuscript_writer",
            "Overwrite restricted output",
            [],
            ["ordinary-output.bin"],
        )


@pytest.mark.parametrize(
    ("field", "status"),
    [("allowed_inputs", "pending"), ("required_outputs", "running")],
)
def test_restricting_artifact_revokes_affected_active_unauthorized_tasks(
    tmp_path: Path,
    field: str,
    status: str,
):
    project = initialize_project(tmp_path)
    router = TaskRouter(project)
    artifact_id = "ordinary.bin"
    task = router.create_task(
        "manuscript_writer",
        "Use artifact",
        [artifact_id] if field == "allowed_inputs" else [],
        [artifact_id] if field == "required_outputs" else ["draft.md"],
    )
    path = project.tasks_dir / f"{task['task_id']}.yaml"
    if status == "running":
        path.write_text(
            yaml.safe_dump({**task, "status": "running"}, sort_keys=False),
            encoding="utf-8",
        )

    router.classify_artifact(artifact_id, "restricted")

    revoked = _load_yaml(path)
    assert revoked["status"] == "revoked"
    assert artifact_id in revoked["revocation_reason"]
    assert "restricted" in revoked["revocation_reason"]


def test_restricting_artifact_keeps_authorized_and_completed_tasks(
    tmp_path: Path,
):
    project = initialize_project(tmp_path)
    router = TaskRouter(project)
    artifact_id = "ordinary.bin"
    authorized = router.create_task(
        "sensitive_data_analyst",
        "Use restricted artifact",
        [artifact_id],
        ["safe-summary.md"],
    )
    completed = router.create_task(
        "manuscript_writer",
        "Past use",
        [artifact_id],
        ["past-summary.md"],
    )
    completed_path = project.tasks_dir / f"{completed['task_id']}.yaml"
    completed_path.write_text(
        yaml.safe_dump({**completed, "status": "completed"}, sort_keys=False),
        encoding="utf-8",
    )

    router.classify_artifact(artifact_id, "restricted")

    assert _load_yaml(project.tasks_dir / f"{authorized['task_id']}.yaml")["status"] == (
        "pending"
    )
    assert _load_yaml(completed_path)["status"] == "completed"


def test_restriction_transaction_recovers_manifest_commit_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    project = initialize_project(tmp_path)
    router = TaskRouter(project)
    artifact_id = "ordinary.bin"
    task = router.create_task(
        "manuscript_writer",
        "Use artifact",
        [artifact_id],
        ["draft.md"],
    )
    task_path = project.tasks_dir / f"{task['task_id']}.yaml"
    journal_path = project.artifacts_dir / ".restriction-transaction.yaml"
    real_atomic_write = task_router_module._atomic_write_text

    def fail_manifest(path, content):
        if path == router._artifact_manifest_path:
            raise OSError("injected manifest commit failure")
        return real_atomic_write(path, content)

    monkeypatch.setattr(task_router_module, "_atomic_write_text", fail_manifest)

    with pytest.raises(OSError, match="manifest commit"):
        router.classify_artifact(artifact_id, "restricted")

    assert journal_path.is_file()
    assert _load_yaml(task_path)["status"] == "pending"
    assert not router._artifact_manifest_path.exists()
    before = set(project.tasks_dir.glob("task-*.yaml"))
    with pytest.raises(OSError, match="manifest commit"):
        router.create_task(
            "manuscript_writer",
            "Must not bypass pending restriction",
            [artifact_id],
            ["other.md"],
        )
    assert set(project.tasks_dir.glob("task-*.yaml")) == before

    monkeypatch.setattr(task_router_module, "_atomic_write_text", real_atomic_write)
    recovery_router = TaskRouter(project)
    with pytest.raises(ValueError, match="restricted"):
        recovery_router.create_task(
            "manuscript_writer",
            "Blocked after recovery",
            [artifact_id],
            ["other.md"],
        )

    assert _load_yaml(task_path)["status"] == "revoked"
    assert _load_yaml(router._artifact_manifest_path)["artifacts"][artifact_id][
        "classification"
    ] == "restricted"
    assert not journal_path.exists()


def test_pending_restriction_journal_cannot_be_hidden_by_exists_result(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    project = initialize_project(tmp_path)
    router = TaskRouter(project)
    artifact_id = "ordinary.bin"
    router.create_task(
        "manuscript_writer",
        "Use artifact",
        [artifact_id],
        ["draft.md"],
    )
    journal_path = project.artifacts_dir / ".restriction-transaction.yaml"
    real_atomic_write = task_router_module._atomic_write_text

    def fail_manifest(path, content):
        if path == router._artifact_manifest_path:
            raise OSError("injected manifest commit failure")
        return real_atomic_write(path, content)

    monkeypatch.setattr(task_router_module, "_atomic_write_text", fail_manifest)
    with pytest.raises(OSError, match="manifest commit"):
        router.classify_artifact(artifact_id, "restricted")
    monkeypatch.setattr(task_router_module, "_atomic_write_text", real_atomic_write)

    real_exists = Path.exists

    def hide_journal(path):
        if path == journal_path:
            return False
        return real_exists(path)

    monkeypatch.setattr(Path, "exists", hide_journal)

    with pytest.raises(ValueError, match="restricted"):
        TaskRouter(project).create_task(
            "manuscript_writer",
            "Must recover hidden pending restriction",
            [artifact_id],
            ["other.md"],
        )


def test_restriction_transaction_recovers_revocation_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    project = initialize_project(tmp_path)
    router = TaskRouter(project)
    artifact_id = "ordinary.bin"
    first_task = router.create_task(
        "manuscript_writer",
        "Use artifact first",
        [artifact_id],
        ["first-draft.md"],
    )
    second_task = router.create_task(
        "ecological_statistician",
        "Use artifact second",
        [artifact_id],
        ["second-analysis.yaml"],
    )
    journal_path = project.artifacts_dir / ".restriction-transaction.yaml"
    real_atomic_write = task_router_module._atomic_write_text
    manifest = router._load_artifact_manifest()
    manifest["artifacts"][artifact_id] = {"classification": "restricted"}
    transaction = router._restriction_transaction(
        artifact_id,
        "restricted",
        manifest,
    )
    first_path, failure_path = [
        project.tasks_dir / record["task_file"]
        for record in transaction["revocations"]
    ]

    def fail_revocation(path, content):
        if path == failure_path:
            raise OSError("injected revocation commit failure")
        return real_atomic_write(path, content)

    monkeypatch.setattr(task_router_module, "_atomic_write_text", fail_revocation)

    with pytest.raises(OSError, match="revocation commit"):
        router.classify_artifact(artifact_id, "restricted")

    assert journal_path.is_file()
    assert _load_yaml(first_path)["status"] == "revoked"
    assert _load_yaml(failure_path)["status"] == "pending"
    assert _load_yaml(router._artifact_manifest_path)["artifacts"][artifact_id][
        "classification"
    ] == "restricted"
    before = set(project.tasks_dir.glob("task-*.yaml"))
    with pytest.raises(OSError, match="revocation commit"):
        router.create_task(
            "manuscript_writer",
            "Must not bypass pending revocation",
            [artifact_id],
            ["other.md"],
        )
    assert set(project.tasks_dir.glob("task-*.yaml")) == before

    monkeypatch.setattr(task_router_module, "_atomic_write_text", real_atomic_write)
    recovery_router = TaskRouter(project)
    with pytest.raises(ValueError, match="restricted"):
        recovery_router.create_task(
            "manuscript_writer",
            "Blocked after recovery",
            [artifact_id],
            ["other.md"],
        )

    assert {
        _load_yaml(project.tasks_dir / f"{first_task['task_id']}.yaml")["status"],
        _load_yaml(project.tasks_dir / f"{second_task['task_id']}.yaml")["status"],
    } == {"revoked"}
    assert not journal_path.exists()


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


def test_task_persistence_is_atomic_with_artifact_reclassification(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    project = initialize_project(tmp_path)
    task_router = TaskRouter(project)
    classification_router = TaskRouter(project)
    artifact_id = "ordinary.bin"
    task_router.register_artifact(artifact_id, "verified")
    persistence_started = Event()
    release_persistence = Event()
    classification_started = Event()
    real_persist = task_router._persist_new_task

    def blocking_persist(task):
        persistence_started.set()
        release_persistence.wait(timeout=5)
        return real_persist(task)

    def reclassify():
        classification_started.set()
        return classification_router.classify_artifact(artifact_id, "restricted")

    monkeypatch.setattr(task_router, "_persist_new_task", blocking_persist)

    with ThreadPoolExecutor(max_workers=2) as pool:
        task_future = pool.submit(
            task_router.create_task,
            "manuscript_writer",
            "Draft",
            [artifact_id],
            ["draft.md"],
        )
        assert persistence_started.wait(timeout=5)
        classification_future = pool.submit(reclassify)
        assert classification_started.wait(timeout=5)
        try:
            with pytest.raises(FutureTimeoutError):
                classification_future.result(timeout=0.2)
        finally:
            release_persistence.set()

        task = task_future.result(timeout=5)
        classification_future.result(timeout=5)

    assert _load_yaml(project.tasks_dir / f"{task['task_id']}.yaml")["status"] == (
        "revoked"
    )


def test_reclassification_that_wins_manifest_lock_blocks_general_task(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    project = initialize_project(tmp_path)
    classification_router = TaskRouter(project)
    task_router = TaskRouter(project)
    artifact_id = "ordinary.bin"
    classification_router.register_artifact(artifact_id, "verified")
    restricted_written = Event()
    release_classification = Event()
    real_atomic_write = task_router_module._atomic_write_text

    def hold_restricted_manifest_lock(path, content):
        real_atomic_write(path, content)
        restricted_written.set()
        release_classification.wait(timeout=5)

    monkeypatch.setattr(
        task_router_module,
        "_atomic_write_text",
        hold_restricted_manifest_lock,
    )

    with ThreadPoolExecutor(max_workers=2) as pool:
        classification_future = pool.submit(
            classification_router.classify_artifact,
            artifact_id,
            "restricted",
        )
        assert restricted_written.wait(timeout=5)
        task_future = pool.submit(
            task_router.create_task,
            "manuscript_writer",
            "Draft",
            [artifact_id],
            ["draft.md"],
        )
        try:
            with pytest.raises(FutureTimeoutError):
                task_future.result(timeout=0.2)
        finally:
            release_classification.set()

        classification_future.result(timeout=5)
        with pytest.raises(ValueError, match="restricted"):
            task_future.result(timeout=5)


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
        _set_task_status(router.project, worker, "completed")
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


def test_sensitive_location_reviewer_rejects_restricted_derived_worker_output(
    tmp_path: Path,
):
    project = initialize_project(tmp_path)
    router = TaskRouter(project)
    sensitive_output = ".wmb/artifacts/sensitive/exact_locations.csv"
    worker = router.create_task(
        "sensitive_data_analyst",
        "Prepare restricted result",
        [],
        [sensitive_output],
    )
    _set_task_status(project, worker, "completed")

    with pytest.raises(ValueError, match="restricted-derived"):
        router.create_task(
            "sensitive_location_reviewer",
            "Check disclosure risk",
            [sensitive_output],
            ["sensitive-review.yaml"],
            review_of=worker["task_id"],
        )


def test_task_id_collision_never_overwrites_existing_task(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    project = initialize_project(tmp_path)
    existing = TaskRouter(project).create_task(
        "manuscript_writer",
        "Existing draft",
        [],
        ["existing.md"],
    )
    collision_path = project.tasks_dir / "task-collision.yaml"
    original = yaml.safe_dump(
        {**existing, "task_id": "task-collision"},
        allow_unicode=True,
        sort_keys=False,
    )
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


def test_transient_read_after_successful_write_does_not_duplicate_context(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    project = initialize_project(tmp_path)
    identifiers = iter(
        [
            SimpleNamespace(hex="context"),
            SimpleNamespace(hex="first"),
            SimpleNamespace(hex="second"),
        ]
    )
    real_read_text = Path.read_text
    failed_once = False

    def transient_task_read(path, *args, **kwargs):
        nonlocal failed_once
        if path.name == "task-first.yaml" and not failed_once:
            failed_once = True
            raise PermissionError("transient confirmation read failure")
        return real_read_text(path, *args, **kwargs)

    monkeypatch.setattr(task_router_module, "uuid4", lambda: next(identifiers))
    monkeypatch.setattr(Path, "read_text", transient_task_read)

    task = TaskRouter(project).create_task(
        "manuscript_writer",
        "Draft",
        [],
        ["draft.md"],
    )

    persisted = list(project.tasks_dir.glob("task-*.yaml"))
    assert task["task_id"] == "task-first"
    assert len(persisted) == 1
    assert _load_yaml(persisted[0])["context_id"] == task["context_id"]


def test_post_publication_write_exception_reconciles_owned_task(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    project = initialize_project(tmp_path)
    real_write_once = task_router_module._write_once

    def publish_then_fail(path, content):
        real_write_once(path, content)
        raise RuntimeError("simulated post-publication failure")

    monkeypatch.setattr(task_router_module, "_write_once", publish_then_fail)

    task = TaskRouter(project).create_task(
        "manuscript_writer",
        "Draft",
        [],
        ["draft.md"],
    )

    persisted = list(project.tasks_dir.glob("task-*.yaml"))
    assert len(persisted) == 1
    assert _load_yaml(persisted[0]) == task


def test_post_publication_exception_retries_transient_reconciliation_read(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    project = initialize_project(tmp_path)
    real_write_once = task_router_module._write_once
    real_read_text = Path.read_text
    failed_once = False

    def publish_then_fail(path, content):
        real_write_once(path, content)
        raise OSError("simulated post-publication failure")

    def transient_read(path, *args, **kwargs):
        nonlocal failed_once
        if path.parent == project.tasks_dir and path.name.startswith("task-") and not failed_once:
            failed_once = True
            raise OSError("simulated transient reconciliation failure")
        return real_read_text(path, *args, **kwargs)

    monkeypatch.setattr(task_router_module, "_write_once", publish_then_fail)
    monkeypatch.setattr(Path, "read_text", transient_read)

    task = TaskRouter(project).create_task(
        "manuscript_writer",
        "Draft",
        [],
        ["draft.md"],
    )

    assert _load_yaml(project.tasks_dir / f"{task['task_id']}.yaml") == task


def test_concurrent_same_content_tasks_get_distinct_task_ids(
    tmp_path: Path,
):
    router = TaskRouter(initialize_project(tmp_path))

    def create():
        return router.create_task(
            "manuscript_writer",
            "Draft",
            [],
            ["draft.md"],
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        tasks = list(pool.map(lambda _: create(), range(2)))

    assert len({task["task_id"] for task in tasks}) == 2
    assert len({task["context_id"] for task in tasks}) == 2


def test_worker_cannot_claim_context_while_reviewer_persistence_is_pending(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    project = initialize_project(tmp_path)
    reviewer_router = TaskRouter(project)
    worker_router = TaskRouter(project)
    reviewed_worker = reviewer_router.create_task(
        "manuscript_writer",
        "Draft reviewed artifact",
        [],
        ["reviewed.md"],
    )
    _set_task_status(project, reviewed_worker, "completed")
    shared_context = "context-pending-reviewer"
    persistence_started = Event()
    release_persistence = Event()
    real_persist = reviewer_router._persist_new_task

    monkeypatch.setattr(
        reviewer_router,
        "_new_context",
        lambda excluded: shared_context,
    )

    def blocking_persist(task):
        persistence_started.set()
        release_persistence.wait(timeout=5)
        return real_persist(task)

    monkeypatch.setattr(reviewer_router, "_persist_new_task", blocking_persist)

    with ThreadPoolExecutor(max_workers=2) as pool:
        reviewer_future = pool.submit(
            reviewer_router.create_task,
            "statistical_reviewer",
            "Review",
            ["reviewed.md"],
            ["review.yaml"],
            reviewed_worker["task_id"],
        )
        assert persistence_started.wait(timeout=5)
        worker_future = pool.submit(
            worker_router.create_task,
            "manuscript_writer",
            "Draft another artifact",
            [],
            ["other.md"],
            context_id=shared_context,
        )
        try:
            with pytest.raises(FutureTimeoutError):
                worker_future.result(timeout=0.2)
        finally:
            release_persistence.set()

        reviewer = reviewer_future.result(timeout=5)
        with pytest.raises(ValueError, match="existing task context"):
            worker_future.result(timeout=5)

    persisted_contexts = {
        _load_yaml(path)["context_id"]
        for path in project.tasks_dir.glob("task-*.yaml")
    }
    assert reviewer["context_id"] == shared_context
    assert len(persisted_contexts) == len(list(project.tasks_dir.glob("task-*.yaml")))


def test_owned_project_lock_release_retries_transient_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    project = initialize_project(tmp_path)
    lock_path = project.tasks_dir / ".test.lock"
    real_remove = task_router_module._remove_lock_if_unchanged
    attempts = 0

    def transient_remove(path, data, identity):
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            return False
        return real_remove(path, data, identity)

    monkeypatch.setattr(
        task_router_module,
        "_remove_lock_if_unchanged",
        transient_remove,
    )

    with task_router_module._owned_project_lock(lock_path):
        pass

    assert attempts == 3
    assert not lock_path.exists()


def test_owned_project_lock_release_failure_raises_clear_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    project = initialize_project(tmp_path)
    lock_path = project.tasks_dir / ".test.lock"
    real_unlink = Path.unlink
    monkeypatch.setattr(
        task_router_module,
        "_remove_lock_if_unchanged",
        lambda path, data, identity: False,
    )

    with pytest.raises(RuntimeError, match="release owned project lock"):
        with task_router_module._owned_project_lock(lock_path):
            pass

    assert lock_path.exists()
    real_unlink(lock_path)


def test_owned_project_lock_release_never_deletes_replacement(
    tmp_path: Path,
):
    project = initialize_project(tmp_path)
    lock_path = project.tasks_dir / ".test.lock"
    replacement = b'{"token":"replacement-owner"}'

    with pytest.raises(RuntimeError, match="release owned project lock"):
        with task_router_module._owned_project_lock(lock_path):
            lock_path.unlink()
            lock_path.write_bytes(replacement)

    assert lock_path.read_bytes() == replacement
    lock_path.unlink()
