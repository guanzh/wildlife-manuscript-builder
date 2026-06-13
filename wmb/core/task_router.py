"""Deterministic capability routing and isolated task-contract creation."""

from __future__ import annotations

import json
import os
import re
import socket
import stat
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
_LOCK_RELEASE_ATTEMPTS = 3
_RECONCILE_ATTEMPTS = 3
_RESTRICTION_TRANSACTION_VERSION = 1
_TASK_ID_PATTERN = re.compile(r"task-[A-Za-z0-9_-]+")
_CAPABILITY_PATTERN = re.compile(r"[a-z][a-z0-9]*(?:_[a-z0-9]+)*")
_UNSAFE_PORTABLE_PATH_CHARACTERS = frozenset('<>"|?*')
_WINDOWS_RESERVED_NAMES = frozenset(
    {"aux", "con", "nul", "prn"}
    | {f"com{number}" for number in range(1, 10)}
    | {f"lpt{number}" for number in range(1, 10)}
    | {"com¹", "com²", "com³", "lpt¹", "lpt²", "lpt³"}
)
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
_REVIEW_STAGE_MARKERS = ("audit", "confirmation", "review", "verification")

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
    "mark_recapture": {"population_modeler"},
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
    "molecular_ecology_edna_metabarcoding": {"molecular_ecologist"},
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
    "integrated_occupancy_or_abundance": {"integrated_modeler"},
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
    "glm_glmm": {"ecological_statistician"},
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
    "before_after_with_effort_control": {"intervention_statistician"},
    "state_space": {"population_statistician"},
    "cjs": {"population_statistician"},
    "popan": {"population_statistician"},
    "robust_design": {"population_statistician"},
    "cjs_popan_robust_design": {"population_statistician"},
    "multi_state": {"population_statistician"},
    "multi_state_models": {"population_statistician"},
    "capture_recapture": {"population_statistician"},
    "mark_recapture": {"population_modeler"},
    "matrix_model": {"population_statistician"},
    "matrix_models": {"population_statistician"},
    "ipm": {"population_statistician"},
    "pva": {"population_statistician"},
    "matrix_models_ipm_pva": {"population_statistician"},
    "joint_species_model": {"community_modeler"},
    "joint_species_models": {"community_modeler"},
    "multivariate_community_model": {"community_modeler"},
    "multivariate_community_models": {"community_modeler"},
    "community_indicators": {"community_modeler"},
    "community_classification_and_ordination": {"community_modeler"},
    "ordination": {"community_modeler"},
    "baci": {"intervention_statistician"},
    "baci_design": {"intervention_statistician"},
    "did": {"intervention_statistician"},
    "interrupted_time_series": {"intervention_statistician"},
    "matched_controls": {"intervention_statistician"},
    "temporal_spatial_overlap": {"activity_pattern_statistician"},
    "activity_pattern_analysis": {"activity_pattern_statistician"},
    "risk_mapping": {"decision_scientist"},
    "prioritization": {"decision_scientist"},
    "cost_effectiveness": {"decision_scientist"},
    "threshold_model": {"decision_scientist"},
    "threshold_models": {"decision_scientist"},
    "multi_indicator_framework": {"integrated_modeler"},
    "landscape_metrics": {"landscape_modeler"},
    "connectivity": {"landscape_modeler"},
    "connectivity_modeling_circuit_theory_least_cost_path_graph_theory": {
        "landscape_modeler"
    },
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


def _canonical_capability(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("capability must be a non-blank string")
    capability = value.strip().lower()
    if not _CAPABILITY_PATTERN.fullmatch(capability):
        raise ValueError(
            "capability must use lowercase letters, digits, and single underscores"
        )
    return capability


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


def _release_owned_project_lock(
    lock_path: Path,
    lock_data: bytes,
    lock_identity: tuple[int, int],
) -> None:
    for attempt in range(_LOCK_RELEASE_ATTEMPTS):
        if _remove_lock_if_unchanged(lock_path, lock_data, lock_identity):
            return
        if attempt + 1 < _LOCK_RELEASE_ATTEMPTS:
            time.sleep(_LOCK_DELAY_SECONDS)
    raise RuntimeError(f"could not release owned project lock: {lock_path}")


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
            _release_owned_project_lock(lock_path, lock_data, created_identity)
            raise
        try:
            os.close(descriptor)
        except Exception:
            _release_owned_project_lock(lock_path, lock_data, created_identity)
            raise
        lock_identity = created_identity
        break
    if lock_identity is None:
        raise TimeoutError(f"timed out acquiring project lock: {lock_path}")

    try:
        yield
    finally:
        _release_owned_project_lock(lock_path, lock_data, lock_identity)


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
        self._restriction_transaction_path = (
            project.artifacts_dir / ".restriction-transaction.yaml"
        )
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
        stage_token = _token(stage, "stage")
        stage_capabilities = _STAGE_CAPABILITIES.get(stage_token)
        if stage_capabilities is None:
            capabilities.add(
                "generic_stage_reviewer"
                if any(marker in stage_token for marker in _REVIEW_STAGE_MARKERS)
                else "generic_stage_specialist"
            )
            warnings.append(f"unknown stage: {stage.strip()}")
        else:
            capabilities.update(stage_capabilities)
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

        artifact_id = self._canonical_artifact_id(artifact_id, "artifact_id")
        classification = _token(classification, "classification")
        if classification not in _ARTIFACT_CLASSIFICATIONS:
            raise ValueError(f"unknown artifact classification: {classification}")
        # Global lock order: task registry, then artifact manifest.
        with _owned_project_lock(self._task_registry_lock_path):
            with _owned_project_lock(self._artifact_manifest_lock_path):
                self._recover_restriction_transaction()
                manifest = self._load_artifact_manifest()
                existing = manifest["artifacts"].get(artifact_id, {}).get(
                    "classification"
                )
                effective = _conservative_classification(existing, classification)
                manifest["artifacts"][artifact_id] = {
                    "classification": effective,
                }
                if effective in _RESTRICTED_CLASSIFICATIONS:
                    transaction = self._restriction_transaction(
                        artifact_id,
                        effective,
                        manifest,
                    )
                    self._write_restriction_transaction(transaction)
                    self._apply_restriction_transaction(transaction)
                else:
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

        capability = _canonical_capability(capability)
        objective = self._nonblank(objective, "objective")
        inputs = self._artifact_list(allowed_inputs, "allowed_inputs")
        outputs = self._artifact_list(required_outputs, "required_outputs")
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
            with _owned_project_lock(self._artifact_manifest_lock_path):
                self._recover_restriction_transaction()
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

                manifest = self._load_artifact_manifest()
                if reviewed_worker is not None:
                    worker_outputs = set(reviewed_worker["required_outputs"])
                    restricted_worker_outputs = {
                        item
                        for item in worker_outputs
                        if self._classification_from_manifest(manifest, item)
                        in _RESTRICTED_CLASSIFICATIONS
                    }
                    if any(
                        self._classification_from_manifest(manifest, item)
                        in _RESTRICTED_CLASSIFICATIONS
                        for item in reviewed_worker["allowed_inputs"]
                    ):
                        restricted_worker_outputs.update(worker_outputs)
                    if restricted_worker_outputs:
                        raise ValueError(
                            "reviewed worker outputs are restricted-derived artifacts: "
                            + ", ".join(sorted(restricted_worker_outputs))
                        )
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
                restricted_outputs = [
                    item
                    for item in outputs
                    if self._classification_from_manifest(manifest, item)
                    in _RESTRICTED_CLASSIFICATIONS
                ]
                if restricted_outputs and capability not in _SENSITIVE_CAPABILITIES:
                    raise ValueError(
                        f"capability {capability} cannot write restricted outputs: "
                        + ", ".join(restricted_outputs)
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
            payload = dict(payload)
            payload["allowed_inputs"] = self._artifact_list(
                payload["allowed_inputs"],
                "allowed_inputs",
            )
            payload["required_outputs"] = self._artifact_list(
                payload["required_outputs"],
                "required_outputs",
            )
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
        if payload.get("status") != "completed":
            raise ValueError("review_of must reference a completed worker task")
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
        artifacts: dict[str, dict[str, str]] = {}
        for artifact_id, record in payload["artifacts"].items():
            if (
                not isinstance(artifact_id, str)
                or not artifact_id.strip()
                or not isinstance(record, dict)
                or record.get("classification") not in _ARTIFACT_CLASSIFICATIONS
            ):
                raise ValueError("artifact manifest contains an invalid classification")
            canonical_id = self._canonical_artifact_id(artifact_id, "artifact_id")
            classification = record["classification"]
            existing = artifacts.get(canonical_id, {}).get("classification")
            artifacts[canonical_id] = {
                "classification": _conservative_classification(
                    existing,
                    classification,
                )
            }
        return {**payload, "artifacts": artifacts}

    def _artifact_classification(self, artifact_id: str) -> str | None:
        artifact_id = self._canonical_artifact_id(artifact_id, "artifact_id")
        with _owned_project_lock(self._task_registry_lock_path):
            with _owned_project_lock(self._artifact_manifest_lock_path):
                self._recover_restriction_transaction()
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

    def _restriction_transaction(
        self,
        artifact_id: str,
        classification: str,
        manifest: Mapping[str, Any],
    ) -> dict[str, Any]:
        reason = (
            f"authorization revoked: artifact {artifact_id} classified "
            f"{classification}"
        )
        revocations: list[dict[str, Any]] = []
        for path in self.project.tasks_dir.glob("task-*.yaml"):
            if not path.is_file():
                raise ValueError(f"task record is not a file: {path}")
            try:
                task = yaml.safe_load(path.read_text(encoding="utf-8"))
                validate_contract("task", task)
            except Exception as exc:
                raise ValueError(f"cannot reauthorize existing task: {path}") from exc
            if (
                task["status"] not in {"pending", "running"}
                or task["capability"] in _SENSITIVE_CAPABILITIES
                or artifact_id
                not in {*task["allowed_inputs"], *task["required_outputs"]}
            ):
                continue
            revoked = {
                **task,
                "status": "revoked",
                "revocation_reason": reason,
            }
            validate_contract("task", revoked)
            revocations.append({"task_file": path.name, "task": revoked})
        return {
            "version": _RESTRICTION_TRANSACTION_VERSION,
            "artifact_id": artifact_id,
            "classification": classification,
            "manifest": dict(manifest),
            "revocations": revocations,
        }

    def _write_restriction_transaction(self, transaction: Mapping[str, Any]) -> None:
        _atomic_write_text(
            self._restriction_transaction_path,
            yaml.safe_dump(dict(transaction), allow_unicode=True, sort_keys=False),
        )

    def _recover_restriction_transaction(self) -> None:
        try:
            journal_status = self._restriction_transaction_path.lstat()
        except FileNotFoundError:
            return
        except OSError as exc:
            raise RuntimeError(
                "cannot inspect restriction transaction journal"
            ) from exc
        if not stat.S_ISREG(journal_status.st_mode):
            raise ValueError("restriction transaction journal must be a file")
        try:
            transaction = yaml.safe_load(
                self._restriction_transaction_path.read_text(encoding="utf-8")
            )
            transaction = self._validated_restriction_transaction(transaction)
        except Exception as exc:
            raise ValueError("restriction transaction journal is invalid") from exc
        self._apply_restriction_transaction(transaction)

    def _validated_restriction_transaction(self, payload: object) -> dict[str, Any]:
        if not isinstance(payload, dict):
            raise ValueError("restriction transaction must be a mapping")
        artifact_id = self._canonical_artifact_id(
            payload.get("artifact_id"),
            "artifact_id",
        )
        classification = payload.get("classification")
        manifest = payload.get("manifest")
        revocations = payload.get("revocations")
        if (
            payload.get("version") != _RESTRICTION_TRANSACTION_VERSION
            or classification not in _RESTRICTED_CLASSIFICATIONS
            or not isinstance(manifest, dict)
            or not isinstance(manifest.get("artifacts"), dict)
            or manifest["artifacts"].get(artifact_id, {}).get("classification")
            != classification
            or not isinstance(revocations, list)
        ):
            raise ValueError("restriction transaction has invalid metadata")
        normalized_revocations: list[dict[str, Any]] = []
        for record in revocations:
            if not isinstance(record, dict):
                raise ValueError("restriction transaction revocation is invalid")
            task_file = record.get("task_file")
            task = record.get("task")
            validate_contract("task", task)
            if (
                not isinstance(task_file, str)
                or task_file != f"{task['task_id']}.yaml"
                or task.get("status") != "revoked"
                or artifact_id
                not in {*task["allowed_inputs"], *task["required_outputs"]}
            ):
                raise ValueError("restriction transaction revocation is invalid")
            normalized_revocations.append({"task_file": task_file, "task": task})
        return {
            "version": _RESTRICTION_TRANSACTION_VERSION,
            "artifact_id": artifact_id,
            "classification": classification,
            "manifest": manifest,
            "revocations": normalized_revocations,
        }

    def _apply_restriction_transaction(
        self,
        transaction: Mapping[str, Any],
    ) -> None:
        _atomic_write_text(
            self._artifact_manifest_path,
            yaml.safe_dump(
                transaction["manifest"],
                allow_unicode=True,
                sort_keys=False,
            ),
        )
        for record in transaction["revocations"]:
            _atomic_write_text(
                self.project.tasks_dir / record["task_file"],
                yaml.safe_dump(
                    record["task"],
                    allow_unicode=True,
                    sort_keys=False,
                ),
            )
        self._restriction_transaction_path.unlink(missing_ok=True)

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
            try:
                _write_once(path, content)
            except Exception:
                owned = self._reconcile_published_task(path, task)
                if owned is not None:
                    return owned
                raise
            try:
                persisted = path.read_text(encoding="utf-8")
            except OSError:
                owned = self._reconcile_published_task(path, task)
                if owned is not None:
                    return owned
                continue
            if persisted == content:
                return task
            owned = self._reconcile_published_task(path, task)
            if owned is not None:
                return owned
        raise FileExistsError("could not allocate a unique task_id")

    def _reconcile_published_task(
        self,
        path: Path,
        expected: Mapping[str, Any],
    ) -> dict[str, Any] | None:
        last_error: Exception | None = None
        for attempt in range(_RECONCILE_ATTEMPTS):
            try:
                payload = yaml.safe_load(path.read_text(encoding="utf-8"))
                validate_contract("task", payload)
            except OSError as exc:
                last_error = exc
                if attempt + 1 < _RECONCILE_ATTEMPTS:
                    time.sleep(_LOCK_DELAY_SECONDS)
                continue
            except Exception as exc:
                raise ValueError(f"cannot reconcile persisted task: {path}") from exc
            if payload.get("creation_token") != expected["creation_token"]:
                return None
            if payload != expected:
                raise ValueError(
                    "task creation token does not identify the expected owned task"
                )
            return payload
        if os.path.lexists(path):
            raise RuntimeError(
                f"could not reconcile published task {path} after write: "
                f"{expected['creation_token']}"
            ) from last_error
        return None

    def _artifact_list(self, values: object, field: str) -> list[str]:
        if isinstance(values, str) or not isinstance(values, Iterable):
            raise ValueError(f"{field} must be a list of non-blank strings")
        canonical: list[str] = []
        seen: set[str] = set()
        for value in values:
            artifact_id = self._canonical_artifact_id(value, field)
            if artifact_id not in seen:
                canonical.append(artifact_id)
                seen.add(artifact_id)
        return canonical

    def _canonical_artifact_id(self, value: object, field: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field} must be a non-blank string")
        if value != value.strip():
            raise ValueError(f"{field} must not have surrounding whitespace")
        artifact_id = value
        if os.name != "nt" and "\\" in artifact_id:
            raise ValueError(f"{field} must use portable path separators")
        candidate = Path(artifact_id)
        if any(part == os.pardir for part in candidate.parts):
            raise ValueError(f"{field} must not contain path traversal")
        path_parts = candidate.parts[1:] if candidate.anchor else candidate.parts
        for part in path_parts:
            reserved_base = part.split(".", 1)[0].rstrip(" ").casefold()
            if (
                not part
                or part.endswith((" ", "."))
                or ":" in part
                or any(
                    character in _UNSAFE_PORTABLE_PATH_CHARACTERS
                    or ord(character) < 32
                    for character in part
                )
                or reserved_base in _WINDOWS_RESERVED_NAMES
            ):
                raise ValueError(f"{field} contains an unsafe path component")
        try:
            resolved = (
                candidate.resolve()
                if candidate.is_absolute()
                else (self.project.root / candidate).resolve()
            )
            relative = resolved.relative_to(self.project.root)
        except (OSError, RuntimeError, ValueError) as exc:
            raise ValueError(
                f"{field} must identify an artifact inside the project"
            ) from exc
        if not relative.parts:
            raise ValueError(f"{field} must identify an artifact inside the project")
        return os.path.normcase(str(relative)).replace(os.sep, "/")

    @staticmethod
    def _nonblank(value: object, field: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field} must be a non-blank string")
        return value.strip()


__all__ = ["CapabilitySelection", "TaskRouter"]
