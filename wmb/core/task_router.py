"""Deterministic capability routing and isolated task-contract creation."""

from __future__ import annotations

import os
import re
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any
from uuid import uuid4

import yaml

from wmb.contracts import validate_contract
from wmb.core.models import ProjectPaths
from wmb.core.project import _write_once

_IDENTIFIER_ATTEMPTS = 1_000
_TASK_ID_PATTERN = re.compile(r"task-[A-Za-z0-9_-]+")

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
    "matrix_model": {"population_statistician"},
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
    "independent_review": {"independent_reviewer"},
    "package_verification": {"package_reviewer"},
    "awaiting_final_confirmation": {"final_package_reviewer"},
    "candidate_level_4": {"package_reviewer"},
    "downgraded": {"deliverable_writer"},
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


def _capabilities_for(
    values: object,
    field: str,
    rules: Mapping[str, set[str]],
) -> set[str]:
    if values is None:
        return set()
    if isinstance(values, str) or not isinstance(values, Iterable):
        raise ValueError(f"{field} must be a list of non-blank strings")
    capabilities: set[str] = set()
    for value in values:
        capabilities.update(rules.get(_token(value, field), set()))
    return capabilities


def _is_reviewer(capability: str) -> bool:
    return capability.endswith("_reviewer")


def _is_restricted(identifier: str) -> bool:
    normalized = _token(identifier, "allowed_inputs")
    return any(marker in normalized for marker in _SENSITIVE_MARKERS)


def _task_path(project: ProjectPaths, task_id: str) -> Path:
    if not _TASK_ID_PATTERN.fullmatch(task_id):
        raise ValueError("review_of must reference an existing worker task")
    return project.tasks_dir / f"{task_id}.yaml"


class TaskRouter:
    """Route ecology capabilities and persist isolated agent tasks."""

    def __init__(self, project: ProjectPaths) -> None:
        if not isinstance(project, ProjectPaths):
            raise TypeError("project must be ProjectPaths")
        if not project.tasks_dir.is_dir():
            raise ValueError("project must be initialized before routing tasks")
        self.project = project

    def select_capabilities(
        self,
        data_types: Iterable[str] | None,
        methods: Iterable[str] | None,
        risks: Iterable[str] | None,
        stage: str,
    ) -> list[str]:
        """Return every applicable capability in stable lexical order."""

        capabilities = _capabilities_for(
            data_types,
            "data_types",
            _DATA_TYPE_CAPABILITIES,
        )
        capabilities.update(
            _capabilities_for(methods, "methods", _METHOD_CAPABILITIES)
        )
        capabilities.update(_capabilities_for(risks, "risks", _RISK_CAPABILITIES))
        capabilities.update(_STAGE_CAPABILITIES.get(_token(stage, "stage"), set()))
        return sorted(capabilities)

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
        reviewed_worker: dict[str, Any] | None = None
        if reviewer:
            reviewed_worker = self._load_reviewed_worker(review_of)
            unlisted = sorted(set(inputs) - set(reviewed_worker["required_outputs"]))
            if unlisted:
                raise ValueError(
                    "reviewer allowed_inputs contain unlisted worker artifacts: "
                    + ", ".join(unlisted)
                )
        elif review_of is not None:
            raise ValueError("review_of requires a reviewer capability")

        restricted = [item for item in inputs if _is_restricted(item)]
        if restricted and capability not in _SENSITIVE_CAPABILITIES:
            raise ValueError(
                f"capability {capability} cannot access restricted inputs: "
                + ", ".join(restricted)
            )

        if context_id is None:
            context_id = self._new_context(
                reviewed_worker["context_id"] if reviewed_worker else None
            )
        else:
            context_id = self._nonblank(context_id, "context_id")
            if reviewed_worker and context_id == reviewed_worker["context_id"]:
                raise ValueError("reviewer context must differ from worker context")

        base_task: dict[str, Any] = {
            "capability": capability,
            "objective": objective,
            "allowed_inputs": inputs,
            "required_outputs": outputs,
            "acceptance_criteria": criteria,
            "prohibited_actions": prohibited,
            "max_attempts": max_attempts,
            "status": "pending",
            "role": "reviewer" if reviewer else "worker",
            "context_id": context_id,
        }
        if reviewed_worker is not None:
            base_task["review_of"] = reviewed_worker["task_id"]

        return self._persist_new_task(base_task)

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

    def _new_context(self, excluded: str | None) -> str:
        for _ in range(_IDENTIFIER_ATTEMPTS):
            context_id = f"context-{uuid4().hex}"
            if context_id != excluded:
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


__all__ = ["TaskRouter"]
