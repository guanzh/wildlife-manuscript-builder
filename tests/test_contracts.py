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
        "decision": "PROCEED",
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

RUN_STATUSES = [
    "intake",
    "awaiting_research_direction",
    "evidence_and_analysis",
    "result_and_claim_build",
    "manuscript_drafting",
    "independent_review",
    "package_verification",
    "awaiting_final_confirmation",
    "candidate_level_4",
    "downgraded",
    "blocked",
]


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


@pytest.mark.parametrize(
    "kind",
    [
        "./run",
        "../schemas/run",
        "subdir/../run",
        "run.schema",
    ],
)
def test_path_like_contract_kind_raises_contract_error(kind):
    with pytest.raises(ContractError, match="unknown contract kind"):
        validate_contract(kind, VALID_CONTRACTS["run"])


@pytest.mark.parametrize(
    ("kind", "status"),
    [
        ("run", "invented_run_status"),
        ("task", "invented_task_status"),
    ],
)
def test_contract_rejects_unknown_canonical_status(kind, status):
    payload = {**VALID_CONTRACTS[kind], "status": status}

    with pytest.raises(ContractError, match="status"):
        validate_contract(kind, payload)


def test_event_rejects_malformed_timestamp():
    payload = {**VALID_CONTRACTS["event"], "timestamp": "not-a-timestamp"}

    with pytest.raises(ContractError, match="timestamp"):
        validate_contract("event", payload)


def test_event_requires_canonical_decision():
    payload = {**VALID_CONTRACTS["event"]}
    del payload["decision"]

    with pytest.raises(ContractError, match="decision"):
        validate_contract("event", payload)


@pytest.mark.parametrize("decision", ["PIVOT", "proceed", ""])
def test_event_rejects_noncanonical_decision(decision):
    payload = {**VALID_CONTRACTS["event"], "decision": decision}

    with pytest.raises(ContractError, match="decision"):
        validate_contract("event", payload)


def test_event_rejects_whitespace_reason():
    payload = {**VALID_CONTRACTS["event"], "reason": "   "}

    with pytest.raises(ContractError, match="reason"):
        validate_contract("event", payload)


@pytest.mark.parametrize(
    ("kind", "field", "entry"),
    [
        ("result", "findings", None),
        ("result", "failures", 42),
        ("analysis_run", "outputs", None),
        ("analysis_run", "warnings", 42),
        ("analysis_run", "errors", None),
        ("analysis_run", "exclusions", 42),
        ("analysis_run", "limitations", None),
        ("review", "findings", 42),
    ],
)
def test_trace_arrays_reject_meaningless_entries(kind, field, entry):
    payload = {**VALID_CONTRACTS[kind], field: [entry]}

    with pytest.raises(ContractError, match=field):
        validate_contract(kind, payload)


@pytest.mark.parametrize("field", ["from_status", "to_status"])
@pytest.mark.parametrize("status", RUN_STATUSES)
def test_event_accepts_canonical_run_statuses(field, status):
    payload = {**VALID_CONTRACTS["event"], field: status}

    validate_contract("event", payload)


@pytest.mark.parametrize("field", ["from_status", "to_status"])
def test_event_rejects_unknown_run_status(field):
    payload = {**VALID_CONTRACTS["event"], field: "invented_run_status"}

    with pytest.raises(ContractError, match=field):
        validate_contract("event", payload)


@pytest.mark.parametrize(
    ("kind", "status"),
    [
        ("result", "completed"),
        ("result", "failed"),
        ("analysis_run", "successful"),
        ("analysis_run", "usable_with_caveat"),
        ("analysis_run", "failed"),
        ("review", "completed"),
        ("review", "failed"),
    ],
)
def test_contract_accepts_canonical_record_status(kind, status):
    payload = {**VALID_CONTRACTS[kind], "status": status}

    validate_contract(kind, payload)


@pytest.mark.parametrize("kind", ["result", "analysis_run", "review"])
def test_contract_rejects_unknown_record_status(kind):
    payload = {**VALID_CONTRACTS[kind], "status": "invented_status"}

    with pytest.raises(ContractError, match="status"):
        validate_contract(kind, payload)


@pytest.mark.parametrize(
    "field",
    ["unresolved_issues", "limitations", "exclusions", "skipped_work"],
)
@pytest.mark.parametrize("entry", [None, 42, "", {}])
def test_result_trace_arrays_reject_meaningless_entries(field, entry):
    payload = {**VALID_CONTRACTS["result"], field: [entry]}

    with pytest.raises(ContractError, match=field):
        validate_contract("result", payload)


@pytest.mark.parametrize(
    "field",
    [
        "allowed_inputs",
        "required_outputs",
        "acceptance_criteria",
        "prohibited_actions",
    ],
)
@pytest.mark.parametrize("entry", ["", 42])
def test_task_string_arrays_reject_invalid_items(field, entry):
    payload = {**VALID_CONTRACTS["task"], field: [entry]}

    with pytest.raises(ContractError, match=field):
        validate_contract("task", payload)


@pytest.mark.parametrize("entry", ["", 42])
def test_result_artifacts_reject_invalid_identifiers(entry):
    payload = {**VALID_CONTRACTS["result"], "artifacts": [entry]}

    with pytest.raises(ContractError, match="artifacts"):
        validate_contract("result", payload)


@pytest.mark.parametrize("field", ["task_ids", "artifact_ids"])
def test_event_identifier_arrays_reject_empty_items(field):
    payload = {**VALID_CONTRACTS["event"], field: [""]}

    with pytest.raises(ContractError, match=field):
        validate_contract("event", payload)


@pytest.mark.parametrize(
    ("kind", "field"),
    [
        ("event", "artifact_hashes"),
        ("analysis_run", "input_hashes"),
    ],
)
@pytest.mark.parametrize("hashes", [{"": "sha256:abc"}, {"data.csv": ""}])
def test_hash_maps_reject_empty_keys_and_values(kind, field, hashes):
    payload = {**VALID_CONTRACTS[kind], field: hashes}

    with pytest.raises(ContractError, match=field):
        validate_contract(kind, payload)


def test_result_rejects_empty_string_confidence():
    payload = {**VALID_CONTRACTS["result"], "confidence": ""}

    with pytest.raises(ContractError, match="confidence"):
        validate_contract("result", payload)
