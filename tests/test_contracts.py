import pytest

from wmb.contracts import ContractError, validate_contract


VALID_CONTRACTS = {
    "run": {
        "run_id": "run-001",
        "status": "intake",
        "current_gate": "data_contract",
        "delivery_level": 0,
    },
    "event": {
        "event_id": "event-001",
        "timestamp": "2026-06-12T09:00:00Z",
        "actor": "orchestrator",
        "event_type": "transition",
        "from_status": "intake",
        "to_status": "awaiting_research_direction",
        "reason": "data contract reconciled",
    },
    "task": {
        "task_id": "analysis-001",
        "capability": "occupancy_statistician",
        "objective": "Fit occupancy models",
        "allowed_inputs": ["data.csv"],
        "required_outputs": ["result.yaml"],
        "acceptance_criteria": ["report uncertainty"],
        "prohibited_actions": ["change_response_variable"],
        "max_attempts": 3,
        "status": "pending",
    },
    "result": {
        "task_id": "analysis-001",
        "status": "completed",
        "artifacts": ["result.yaml"],
        "findings": ["occupancy varies by habitat"],
        "unresolved_issues": [],
        "recommended_transition": "PROCEED",
        "confidence": "high",
        "limitations": ["single season"],
        "failures": [],
        "exclusions": [],
        "skipped_work": [],
    },
    "analysis_run": {
        "analysis_id": "analysis-run-001",
        "status": "successful",
        "command": "Rscript occupancy.R",
        "input_hashes": {"data.csv": "sha256:abc"},
        "outputs": ["result.yaml"],
        "warnings": [],
        "errors": [],
        "exclusions": [],
        "limitations": [],
    },
    "review": {
        "review_id": "review-001",
        "status": "completed",
        "review_of": "result.yaml",
        "findings": [],
        "verdict": "pass",
        "recommended_transition": "PROCEED",
    },
}


@pytest.mark.parametrize(("kind", "payload"), VALID_CONTRACTS.items())
def test_valid_contract_passes(kind, payload):
    validate_contract(kind, payload)


def test_contracts_allow_additive_metadata():
    payload = {**VALID_CONTRACTS["task"], "adapter_metadata": {"job_id": "42"}}

    validate_contract("task", payload)


def test_invalid_task_contract_reports_sorted_field_paths():
    with pytest.raises(ContractError) as exc_info:
        validate_contract("task", {"task_id": "analysis-001", "max_attempts": 0})

    lines = str(exc_info.value).splitlines()[1:]
    assert lines == sorted(lines)
    assert any("capability:" in line for line in lines)
    assert any("max_attempts:" in line for line in lines)


def test_unknown_contract_kind_raises_contract_error():
    with pytest.raises(ContractError, match="unknown contract kind"):
        validate_contract("missing", {})
