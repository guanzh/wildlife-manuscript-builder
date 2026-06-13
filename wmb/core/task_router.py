"""Deterministic capability routing and isolated task-contract creation."""

from __future__ import annotations

import json
import os
import re
import socket
import time
from collections.abc import Iterable, Mapping
from contextlib import contextmanager
from pathlib import Path
from secrets import token_hex
from tempfile import NamedTemporaryFile
from typing import Any
from uuid import uuid4

import yaml

from wmb.contracts import validate_contract
from wmb.core.models import ProjectPaths
from wmb.core.project import _write_once
from wmb.core.state_store import (
    _exclusive_flags as _lock_exclusive_flags,
    _lock_snapshot,
    _remove_lock_if_unchanged,
    _stale_lock_is_recoverable,
    _write_descriptor as _write_lock_descriptor,
)

_IDENTIFIER_ATTEMPTS = 1_000
_LOCK_ATTEMPTS = 1_000
_LOCK_DELAY_SECONDS = 0.001
_TASK_ID_PATTERN = re.compile(r"task-[A-Za-z0-9_-]+")
_ARTIFACT_CLASSIFICATIONS = frozenset(
    {
        "manuscript",
        "public",
        "raw",
        "raw_project_data",
        "restricted",
        "review_criteria",
        "review_only",
        "sensitive",
        "verified",
        "verified_analysis",
    }
)
_REVIEWER_SUPPLEMENTAL_CLASSIFICATIONS = frozenset(
    {"verified", "verified_analysis", "review_criteria", "review_only"}
)
_RESTRICTED_CLASSIFICATIONS = frozenset({"restricted", "sensitive"})

_DATA_TYPE_CAPABILITIES = {
    "camera_trap": {"camera_trap_ecologist"},
    "camera_trap_data": {"camera_trap_ecologist"},
    "acoustic": {"acoustic_ecologist"},
    "acoustic_monitoring": {"acoustic_ecologist"},
    "transect": {"survey_ecologist"},
    "point_count": {"survey_ecologist"},
    "direct_survey": {"survey_ecologist"},
    "transect_point_count_and_direct_survey": {"survey_ecologist"},
    "occupancy": {"occupancy_ecologist"},
    "distribution": {"occupancy_ecologist"},
    "habitat_suitability": {"occupancy_ecologist"},
    "occupancy_distribution_and_habitat_suitability": {"occupancy_ecologist"},
    "remote_sensing": {"remote_sensing_ecologist"},
    "habitat": {"remote_sensing_ecologist"},
    "remote_sensing_and_habitat": {"remote_sensing_ecologist"},
    "patrol": {"conservation_management_specialist"},
    "threat": {"conservation_management_specialist"},
    "management": {"conservation_management_specialist"},
    "patrol_threat_and_management_data": {"conservation_management_specialist"},
    "multi_source": {"integrated_modeler"},
    "multi_source_data": {"integrated_modeler"},
    "plant_community": {"plant_community_ecologist"},
    "plant_vegetation": {"plant_community_ecologist"},
    "vegetation": {"plant_community_ecologist"},
    "plant_community_vegetation_survey": {"plant_community_ecologist"},
    "population_ecology": {"population_ecologist"},
    "mark_recapture": {"population_ecologist"},
    "population_ecology_mark_recapture_matrix_models": {"population_ecologist"},
    "ecosystem_function": {"ecosystem_function_ecologist"},
    "ecosystem_function_productivity_nutrient_cycling": {
        "ecosystem_function_ecologist"
    },
    "landscape_ecology": {"landscape_ecologist"},
    "landscape_ecology_fragmentation_connectivity": {"landscape_ecologist"},
    "freshwater_ecology": {"freshwater_ecologist"},
    "soil_ecology": {"soil_ecologist"},
    "behavioral_ecology": {"behavioral_ecologist"},
    "disease_ecology": {"disease_ecologist"},
    "molecular_ecology": {"molecular_ecologist"},
    "edna": {"molecular_ecologist"},
    "metabarcoding": {"molecular_ecologist"},
    "urban_ecology": {"urban_ecologist"},
    "paleoecology": {"paleoecologist"},
    "agroecology": {"agroecologist"},
}

_METHOD_CAPABILITIES = {
    "occupancy": {"occupancy_statistician"},
    "dynamic_occupancy": {"occupancy_statistician"},
    "two_species_occupancy": {"occupancy_statistician"},
    "integrated_occupancy": {"occupancy_statistician", "integrated_modeler"},
    "sdm": {"spatial_modeler"},
    "spatial_glm": {"spatial_modeler"},
    "spatial_glmm": {"spatial_modeler"},
    "spatial_glm_glmm": {"spatial_modeler"},
    "habitat_suitability": {"spatial_modeler"},
    "activity_curves": {"activity_pattern_statistician"},
    "overlap_coefficients": {"activity_pattern_statistician"},
    "circular_statistics": {"activity_pattern_statistician"},
    "glm": {"ecological_statistician"},
    "glmm": {"ecological_statistician"},
    "gam": {"ecological_statistician"},
    "scr": {"abundance_statistician"},
    "distance_sampling": {"abundance_statistician"},
    "n_mixture": {"abundance_statistician"},
    "rem": {"abundance_statistician"},
    "rest": {"abundance_statistician"},
    "rem_rest": {"abundance_statistician"},
    "time_to_event": {"abundance_statistician"},
    "space_to_event": {"abundance_statistician"},
    "time_space_to_event": {"abundance_statistician"},
    "state_space": {"population_statistician"},
    "cjs": {"population_statistician"},
    "popan": {"population_statistician"},
    "robust_design": {"population_statistician"},
    "multi_state": {"population_statistician"},
    "multi_state_models": {"population_statistician"},
    "capture_recapture": {"population_statistician"},
    "matrix_model": {"population_statistician"},
    "matrix_models": {"population_statistician"},
    "ipm": {"population_statistician"},
    "pva": {"population_statistician"},
    "joint_species_model": {"community_modeler"},
    "joint_species_models": {"community_modeler"},
    "multivariate_community_model": {"community_modeler"},
    "ordination": {"community_modeler"},
    "baci": {"intervention_statistician"},
    "did": {"intervention_statistician"},
    "interrupted_time_series": {"intervention_statistician"},
    "risk_mapping": {"decision_scientist"},
    "prioritization": {"decision_scientist"},
    "cost_effectiveness": {"decision_scientist"},
    "threshold_model": {"decision_scientist"},
    "threshold_models": {"decision_scientist"},
    "connectivity": {"landscape_modeler"},
    "circuit_theory": {"landscape_modeler"},
    "least_cost_path": {"landscape_modeler"},
    "graph_theory": {"landscape_modeler"},
}

_RISK_CAPABILITIES = {
    "sensitive_location": {"sensitive_location_reviewer"},
    "restricted_data": {"sensitive_location_reviewer"},
    "permit": {"compliance_reviewer"},
    "ethics": {"compliance_reviewer"},
    "data_authorization": {"compliance_reviewer"},
    "citation": {"citation_reviewer"},
    "overclaim": {"claim_boundary_reviewer"},
}

_STAGE_CAPABILITIES = {
    "intake": {"data_contract_reviewer"},
    "awaiting_research_direction": {
        "research_direction_reviewer",
        "research_direction_writer",
    },
    "evidence_and_analysis": {"analysis_reviewer"},
    "result_and_claim_build": {"claim_reviewer", "result_card_writer"},
    "manuscript_drafting": {"manuscript_writer"},
    "independent_review": {"independent_reviewer", "statistical_reviewer"},
    "package_verification": {"package_reviewer", "statistical_reviewer"},
    "awaiting_final_confirmation": {
        "final_package_reviewer",
        "statistical_reviewer",
    },
    "candidate_level_4": {"package_reviewer", "statistical_reviewer"},
    "downgraded": {"deliverable_writer"},
    "blocked": {"blocker_reviewer"},
}

_SENSITIVE_CAPABILITIES = frozenset(
    {
        "restricted_data_steward",
        "sensitive_data_analyst",
        "sensitive_location_reviewer",
    }
)
_SENSITIVE_MARKERS = (
    "confidential",
    "exact_coordinate",
    "exact_location",
    "patrol_route",
    "private",
    "raw_coordinate",
    "restricted",
    "sensitive",
)


def _token(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-blank string")
    return re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")


def _string_list(values: object, field: str) -> list[str]:
    if isinstance(values, str) or not isinstance(values, Iterable):
        raise ValueError(f"{field} must be a list of non-blank strings")
    normalized: list[str] = []
    seen: set[str] = set()
    for value in values:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field} must be a list of non-blank strings")
        item = value.strip()
        if item not in seen:
            normalized.append(item)
            seen.add(item)
    return normalized


def _routed_capabilities(
    values: object,
    field: str,
    rules: Mapping[str, set[str]],
    fallback: str | None = None,
) -> tuple[set[str], list[str]]:
    if values is None:
        return set(), []
    if isinstance(values, str) or not isinstance(values, Iterable):
        raise ValueError(f"{field} must be a list of non-blank strings")
    capabilities: set[str] = set()
    warnings: list[str] = []
    label = field.removesuffix("s").replace("_", " ")
    for value in values:
        token = _token(value, field)
        matched = rules.get(token)
        if matched is not None:
            capabilities.update(matched)
            continue
        if fallback is not None:
            capabilities.add(fallback)
            warnings.append(f"unknown {label}: {value.strip()}")
    return capabilities, warnings


def _is_reviewer(capability: str) -> bool:
    return capability.endswith("_reviewer")


def _is_restricted(identifier: str) -> bool:
    normalized = _token(identifier, "allowed_inputs")
    return any(marker in normalized for marker in _SENSITIVE_MARKERS)


def _task_path(project: ProjectPaths, task_id: str) -> Path:
    if not _TASK_ID_PATTERN.fullmatch(task_id):
        raise ValueError("review_of must reference an existing worker task")
    return project.tasks_dir / f"{task_id}.yaml"


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


@contextmanager
def _owned_project_lock(lock_path: Path):
    lock_data = json.dumps(
        {
            "pid": os.getpid(),
            "host": socket.gethostname(),
            "created_at": time.time(),
            "token": token_hex(16),
        },
        sort_keys=True,
    ).encode("utf-8")
    lock_identity: tuple[int, int] | None = None
    for _ in range(_LOCK_ATTEMPTS):
        try:
            descriptor = os.open(lock_path, _lock_exclusive_flags(), 0o600)
        except (FileExistsError, PermissionError):
            try:
                snapshot = _lock_snapshot(lock_path)
            except PermissionError:
                time.sleep(_LOCK_DELAY_SECONDS)
                continue
            if snapshot is None:
                time.sleep(_LOCK_DELAY_SECONDS)
                continue
            existing_data, existing_identity, modified_at = snapshot
            if _stale_lock_is_recoverable(existing_data, modified_at):
                _remove_lock_if_unchanged(
                    lock_path,
                    existing_data,
                    existing_identity,
                )
                continue
            time.sleep(_LOCK_DELAY_SECONDS)
            continue
        created = os.fstat(descriptor)
        created_identity = (created.st_dev, created.st_ino)
        try:
            _write_lock_descriptor(descriptor, lock_data)
        except Exception:
            try:
                os.close(descriptor)
            except OSError:
                pass
            _remove_lock_if_unchanged(lock_path, lock_data, created_identity)
            raise
        try:
            os.close(descriptor)
        except Exception:
            _remove_lock_if_unchanged(lock_path, lock_data, created_identity)
            raise
        lock_identity = created_identity
        break
    if lock_identity is None:
        raise TimeoutError(f"timed out acquiring project lock: {lock_path}")

    try:
        yield
    finally:
        _remove_lock_if_unchanged(lock_path, lock_data, lock_identity)


def _conservative_classification(existing: str | None, requested: str) -> str:
    if existing == "restricted" or requested == "restricted":
        return "restricted"
    if existing == "sensitive" or requested == "sensitive":
        return "sensitive"
    return requested


class CapabilitySelection(list[str]):
    """List-compatible routed capabilities with explicit routing warnings."""

    def __init__(self, capabilities: Iterable[str], warnings: Iterable[str]) -> None:
        super().__init__(capabilities)
        self.warnings = tuple(warnings)
        self.routing_warnings = self.warnings


class TaskRouter:
    """Route ecology capabilities and persist isolated agent tasks."""

    def __init__(self, project: ProjectPaths) -> None:
        if not isinstance(project, ProjectPaths):
            raise TypeError("project must be ProjectPaths")
        if not project.tasks_dir.is_dir():
            raise ValueError("project must be initialized before routing tasks")
        self.project = project
        self._artifact_manifest_path = project.artifacts_dir / "manifest.yaml"
        self._artifact_manifest_lock_path = project.artifacts_dir / ".manifest.lock"
        self._task_registry_lock_path = project.tasks_dir / ".registry.lock"

    def select_capabilities(
        self,
        data_types: Iterable[str] | None,
        methods: Iterable[str] | None,
        risks: Iterable[str] | None,
        stage: str,
        target_journal: str | None = None,
    ) -> CapabilitySelection:
        """Return every applicable capability in stable lexical order."""

        capabilities, warnings = _routed_capabilities(
            data_types,
            "data_types",
            _DATA_TYPE_CAPABILITIES,
            "generic_ecology_specialist",
        )
        method_capabilities, method_warnings = _routed_capabilities(
            methods,
            "methods",
            _METHOD_CAPABILITIES,
            "generic_method_specialist",
        )
        capabilities.update(method_capabilities)
        warnings.extend(method_warnings)
        risk_capabilities, risk_warnings = _routed_capabilities(
            risks,
            "risks",
            _RISK_CAPABILITIES,
            "generic_risk_reviewer",
        )
        capabilities.update(risk_capabilities)
        warnings.extend(risk_warnings)
        capabilities.update(_STAGE_CAPABILITIES.get(_token(stage, "stage"), set()))
        if target_journal is not None:
            self._nonblank(target_journal, "target_journal")
            capabilities.add("journal_requirements_reviewer")
        return CapabilitySelection(sorted(capabilities), sorted(set(warnings)))

    def classify_artifact(
        self,
        artifact_id: str,
        classification: str,
    ) -> dict[str, Any]:
        """Persist an authoritative access classification for one artifact."""

        artifact_id = self._nonblank(artifact_id, "artifact_id")
        classification = _token(classification, "classification")
        if classification not in _ARTIFACT_CLASSIFICATIONS:
            raise ValueError(f"unknown artifact classification: {classification}")
        with _owned_project_lock(self._artifact_manifest_lock_path):
            manifest = self._load_artifact_manifest()
            existing = manifest["artifacts"].get(artifact_id, {}).get(
                "classification"
            )
            manifest["artifacts"][artifact_id] = {
                "classification": _conservative_classification(
                    existing,
                    classification,
                ),
            }
            _atomic_write_text(
                self._artifact_manifest_path,
                yaml.safe_dump(manifest, allow_unicode=True, sort_keys=False),
            )
        return dict(manifest["artifacts"][artifact_id])

    def register_artifact(
        self,
        artifact_id: str,
        classification: str,
    ) -> dict[str, Any]:
        """Register an artifact classification in the project manifest."""

        return self.classify_artifact(artifact_id, classification)

    def create_task(
        self,
        capability: str,
        objective: str,
        allowed_inputs: Iterable[str],
        required_outputs: Iterable[str],
        review_of: str | None = None,
        acceptance_criteria: Iterable[str] | None = None,
        prohibited_actions: Iterable[str] | None = None,
        max_attempts: int = 3,
        context_id: str | None = None,
    ) -> dict[str, Any]:
        """Validate and persist one worker or isolated reviewer task."""

        capability = _token(capability, "capability")
        objective = self._nonblank(objective, "objective")
        inputs = _string_list(allowed_inputs, "allowed_inputs")
        outputs = _string_list(required_outputs, "required_outputs")
        criteria = _string_list(
            [] if acceptance_criteria is None else acceptance_criteria,
            "acceptance_criteria",
        )
        prohibited = _string_list(
            [] if prohibited_actions is None else prohibited_actions,
            "prohibited_actions",
        )

        reviewer = _is_reviewer(capability)
        if not reviewer and review_of is not None:
            raise ValueError("review_of requires a reviewer capability")

        supplied_context = (
            self._nonblank(context_id, "context_id")
            if context_id is not None
            else None
        )
        # Global lock order: task registry, then artifact manifest.
        with _owned_project_lock(self._task_registry_lock_path):
            existing_contexts = self._existing_task_contexts()
            if supplied_context in existing_contexts:
                raise ValueError("task cannot reuse an existing task context")

            reviewed_worker: dict[str, Any] | None = None
            if reviewer:
                reviewed_worker = self._load_reviewed_worker(review_of)
                excluded_contexts = set(existing_contexts)
                if supplied_context is not None:
                    excluded_contexts.add(supplied_context)
                context_id = self._new_context(excluded_contexts)
            else:
                context_id = supplied_context or self._new_context(existing_contexts)

            if context_id in existing_contexts:
                raise ValueError("task cannot reuse an existing task context")

            with _owned_project_lock(self._artifact_manifest_lock_path):
                manifest = self._load_artifact_manifest()
                if reviewed_worker is not None:
                    worker_outputs = set(reviewed_worker["required_outputs"])
                    unauthorized = sorted(
                        item
                        for item in inputs
                        if item not in worker_outputs
                        and self._classification_from_manifest(manifest, item)
                        not in _REVIEWER_SUPPLEMENTAL_CLASSIFICATIONS
                    )
                    if unauthorized:
                        raise ValueError(
                            "reviewer allowed_inputs contain unauthorized artifacts: "
                            + ", ".join(unauthorized)
                        )

                restricted = [
                    item
                    for item in inputs
                    if self._classification_from_manifest(manifest, item)
                    in _RESTRICTED_CLASSIFICATIONS
                ]
                if restricted and capability not in _SENSITIVE_CAPABILITIES:
                    raise ValueError(
                        f"capability {capability} cannot access restricted inputs: "
                        + ", ".join(restricted)
                    )

                return self._persist_new_task(
                    self._task_payload(
                        capability,
                        objective,
                        inputs,
                        outputs,
                        criteria,
                        prohibited,
                        max_attempts,
                        context_id,
                        reviewed_worker,
                    )
                )

    def _task_payload(
        self,
        capability: str,
        objective: str,
        inputs: list[str],
        outputs: list[str],
        criteria: list[str],
        prohibited: list[str],
        max_attempts: int,
        context_id: str,
        reviewed_worker: Mapping[str, Any] | None,
    ) -> dict[str, Any]:
        task: dict[str, Any] = {
            "capability": capability,
            "objective": objective,
            "allowed_inputs": inputs,
            "required_outputs": outputs,
            "acceptance_criteria": criteria,
            "prohibited_actions": prohibited,
            "max_attempts": max_attempts,
            "status": "pending",
            "role": "reviewer" if reviewed_worker is not None else "worker",
            "context_id": context_id,
            "creation_token": f"creation-{token_hex(16)}",
        }
        if reviewed_worker is not None:
            task["review_of"] = reviewed_worker["task_id"]
        return task

    def _load_reviewed_worker(self, review_of: object) -> dict[str, Any]:
        if not isinstance(review_of, str):
            raise ValueError("review_of must reference an existing worker task")
        path = _task_path(self.project, review_of)
        if not path.is_file():
            raise ValueError("review_of must reference an existing worker task")
        try:
            payload = yaml.safe_load(path.read_text(encoding="utf-8"))
            validate_contract("task", payload)
        except Exception as exc:
            raise ValueError(
                "review_of must reference an existing worker task"
            ) from exc
        if (
            not isinstance(payload, dict)
            or payload.get("task_id") != review_of
            or payload.get("role") != "worker"
            or "review_of" in payload
            or not isinstance(payload.get("context_id"), str)
            or not payload["context_id"].strip()
        ):
            raise ValueError("review_of must reference an existing worker task")
        return payload

    def _load_artifact_manifest(self) -> dict[str, Any]:
        if not self._artifact_manifest_path.exists():
            return {"artifacts": {}}
        if not self._artifact_manifest_path.is_file():
            raise ValueError("artifact manifest must be a file")
        payload = yaml.safe_load(
            self._artifact_manifest_path.read_text(encoding="utf-8")
        )
        if not isinstance(payload, dict) or not isinstance(
            payload.get("artifacts"), dict
        ):
            raise ValueError("artifact manifest must contain an artifacts mapping")
        for artifact_id, record in payload["artifacts"].items():
            if (
                not isinstance(artifact_id, str)
                or not artifact_id.strip()
                or not isinstance(record, dict)
                or record.get("classification") not in _ARTIFACT_CLASSIFICATIONS
            ):
                raise ValueError("artifact manifest contains an invalid classification")
        return payload

    def _artifact_classification(self, artifact_id: str) -> str | None:
        with _owned_project_lock(self._artifact_manifest_lock_path):
            manifest = self._load_artifact_manifest()
            return self._classification_from_manifest(manifest, artifact_id)

    @staticmethod
    def _classification_from_manifest(
        manifest: Mapping[str, Any],
        artifact_id: str,
    ) -> str | None:
        record = manifest["artifacts"].get(artifact_id)
        classification = record["classification"] if record is not None else None
        if _is_restricted(artifact_id):
            return "restricted"
        return classification

    def _existing_task_contexts(self) -> set[str]:
        contexts: set[str] = set()
        for path in self.project.tasks_dir.glob("task-*.yaml"):
            if not path.is_file():
                raise ValueError(f"task record is not a file: {path}")
            try:
                payload = yaml.safe_load(path.read_text(encoding="utf-8"))
                validate_contract("task", payload)
                context_id = payload["context_id"]
            except Exception as exc:
                raise ValueError(
                    f"cannot inspect existing task context: {path}"
                ) from exc
            contexts.add(context_id)
        return contexts

    def _new_context(self, excluded: Iterable[str]) -> str:
        excluded_contexts = set(excluded)
        for _ in range(_IDENTIFIER_ATTEMPTS):
            context_id = f"context-{uuid4().hex}"
            if context_id not in excluded_contexts:
                return context_id
        raise FileExistsError("could not allocate an isolated context_id")

    def _persist_new_task(self, base_task: Mapping[str, Any]) -> dict[str, Any]:
        for _ in range(_IDENTIFIER_ATTEMPTS):
            task = {"task_id": f"task-{uuid4().hex}", **base_task}
            validate_contract("task", task)
            path = self.project.tasks_dir / f"{task['task_id']}.yaml"
            if os.path.lexists(path):
                continue
            content = yaml.safe_dump(task, allow_unicode=True, sort_keys=False)
            _write_once(path, content)
            try:
                persisted = path.read_text(encoding="utf-8")
            except (FileNotFoundError, IsADirectoryError, PermissionError):
                continue
            if persisted == content:
                return task
        raise FileExistsError("could not allocate a unique task_id")

    @staticmethod
    def _nonblank(value: object, field: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field} must be a non-blank string")
        return value.strip()


__all__ = ["CapabilitySelection", "TaskRouter"]
