# Wildlife Manuscript Builder Multi-Agent Workflow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a resumable, finite, platform-neutral multi-agent workflow inside Wildlife Manuscript Builder, with executable Codex and Hermes adapters and honest submission-readiness gates.

**Architecture:** A Python package named `wmb` owns schemas, canonical `.wmb/` project state, legal transitions, Gate policy, finite loops, provenance, recovery, and package verification. Platform adapters dispatch or synchronize tasks but cannot alter scientific policy. Existing ecology guidance remains in `SKILL.md` and `references/`, while deterministic portions gain executable enforcement.

**Tech Stack:** Python 3.11, standard library, PyYAML, jsonschema, pytest, YAML/JSON project records, Hermes CLI.

---

## File Map

### Package and entry points

- Create `pyproject.toml`: package metadata, runtime dependencies, pytest settings, `wmb` CLI.
- Create `wmb/__init__.py`: public version and package exports.
- Create `wmb/__main__.py`: `python -m wmb` entry point.
- Create `wmb/cli.py`: user-facing init/status/task/result/resume/verify/dispatch commands.

### Schemas and contracts

- Create `wmb/schemas/run.schema.json`: canonical run state.
- Create `wmb/schemas/event.schema.json`: append-only event entries.
- Create `wmb/schemas/task.schema.json`: agent task contract.
- Create `wmb/schemas/result.schema.json`: agent result contract.
- Create `wmb/schemas/analysis_run.schema.json`: analysis provenance.
- Create `wmb/schemas/review.schema.json`: review finding and verdict.
- Create `wmb/contracts.py`: schema loading and validation.

### Core workflow

- Create `wmb/core/models.py`: enums and immutable transition/result types.
- Create `wmb/core/project.py`: initialize and load `.wmb/` projects.
- Create `wmb/core/state_machine.py`: legal transitions.
- Create `wmb/core/state_store.py`: sole canonical state writer and event append.
- Create `wmb/core/task_router.py`: dynamic capability selection and task creation.
- Create `wmb/core/gate_engine.py`: author-confirmation and Gate policy.
- Create `wmb/core/loop_controller.py`: finite revision-loop policy.
- Create `wmb/core/provenance.py`: analysis and claim trace validation.
- Create `wmb/core/journal.py`: default journal contract and official-source refresh.
- Create `wmb/core/verifier.py`: deterministic and heuristic package checks.
- Create `wmb/core/recovery.py`: state validation, task recovery, and adapter reconciliation.
- Create `wmb/core/logging.py`: rejection, exception, retry, and skip ledger.

### Platform adapters

- Create `wmb/adapters/base.py`: adapter protocol and shared dispatch/result types.
- Create `wmb/adapters/codex.py`: executable Codex dispatch packet generation and result ingestion.
- Create `wmb/adapters/hermes.py`: Hermes Durable Kanban command mapping, dispatch, and status reconciliation.

### Documentation migration

- Modify `SKILL.md`: explain executable workflow, defaults, author gates, and platform commands.
- Create `references/rewriting-existing-manuscript.md`: repair missing rewrite guidance.
- Create `references/literature-search-fallback.md`: repair missing literature fallback guidance without embedding secrets.
- Modify `references/run-lessons.md`: require approval and explicit enablement.
- Modify `references/journal-target-contract.md`: set 《生物多样性》 defaults and stale-cache policy.
- Create `references/multi-agent-workflow.md`: concise operator guide.

### Tests and fixtures

- Create focused tests under `tests/`.
- Create `tests/conftest.py` for reusable initialized-project and result fixtures.
- Create `tests/fixtures/basic_project/` for cross-platform and recovery tests.

## Task 1: Package Scaffold and Schema Validation

**Files:**
- Create: `pyproject.toml`
- Create: `wmb/__init__.py`
- Create: `wmb/core/__init__.py`
- Create: `wmb/adapters/__init__.py`
- Create: `wmb/contracts.py`
- Create: `wmb/schemas/run.schema.json`
- Create: `wmb/schemas/event.schema.json`
- Create: `wmb/schemas/task.schema.json`
- Create: `wmb/schemas/result.schema.json`
- Create: `wmb/schemas/analysis_run.schema.json`
- Create: `wmb/schemas/review.schema.json`
- Test: `tests/test_contracts.py`

- [ ] **Step 1: Write failing schema-validation tests**

```python
from wmb.contracts import ContractError, validate_contract


def test_valid_task_contract_passes():
    validate_contract(
        "task",
        {
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
    )


def test_invalid_task_contract_raises():
    try:
        validate_contract("task", {"task_id": "analysis-001"})
    except ContractError as exc:
        assert "capability" in str(exc)
    else:
        raise AssertionError("invalid task contract passed")
```

- [ ] **Step 2: Run the tests and verify they fail**

Run: `python -m pytest tests/test_contracts.py -q`  
Expected: FAIL because `wmb.contracts` does not exist.

- [ ] **Step 3: Add package metadata, schemas, and validator**

Implement `validate_contract(kind, payload)` by loading
`wmb/schemas/{kind}.schema.json` with `jsonschema.Draft202012Validator`.
Raise a `ContractError` containing sorted field paths and messages.

The task schema must require the fields shown in the test. The remaining
schemas must require their identity, status, and relevant trace fields while
allowing additive metadata through `additionalProperties: true`.

- [ ] **Step 4: Run schema tests**

Run: `python -m pytest tests/test_contracts.py -q`  
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml wmb tests/test_contracts.py
git commit -m "feat: add WMB package and contract schemas"
```

## Task 2: Project Initialization and Defaults

**Files:**
- Create: `wmb/core/models.py`
- Create: `wmb/core/project.py`
- Test: `tests/test_project.py`

- [ ] **Step 1: Write failing initialization tests**

```python
from pathlib import Path
import yaml

from wmb.core.project import initialize_project


def test_initialize_project_creates_cross_platform_state(tmp_path: Path):
    project = initialize_project(tmp_path)
    run = yaml.safe_load((project.wmb_dir / "run.yaml").read_text("utf-8"))
    author = yaml.safe_load(
        (project.wmb_dir / "author_confirmation_queue.yaml").read_text("utf-8")
    )
    journal = yaml.safe_load(
        (project.wmb_dir / "journal_contract.yaml").read_text("utf-8")
    )

    assert run["status"] == "intake"
    assert run["current_gate"] == "data_contract"
    assert run["delivery_level"] == 0
    assert author["items"][0]["field"] == "author_identity"
    assert author["items"][0]["placeholder"] == "Dr. Who"
    assert journal["journal_name"] == "生物多样性"
    assert journal["main_language"] == "zh-CN"
```

- [ ] **Step 2: Run and verify failure**

Run: `python -m pytest tests/test_project.py -q`  
Expected: FAIL because project initialization does not exist.

- [ ] **Step 3: Implement initialization**

Implement `ProjectPaths` and `initialize_project(root, author=None, journal=None)`.
It must create all `.wmb/` subdirectories, validated `run.yaml`, an empty
append-only `logs/events.jsonl`, an empty `logs/rejections.jsonl`, default
`Dr. Who` confirmation items, and the default 《生物多样性》 contract.

Initialization must be idempotent and must not overwrite an existing run.

- [ ] **Step 4: Run tests**

Run: `python -m pytest tests/test_project.py -q`  
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add wmb/core tests/test_project.py
git commit -m "feat: initialize persistent WMB projects"
```

## Task 3: Legal State Machine and Single State Writer

**Files:**
- Create: `wmb/core/state_machine.py`
- Create: `wmb/core/state_store.py`
- Test: `tests/test_state_store.py`

- [ ] **Step 1: Write failing state tests**

```python
import pytest

from wmb.core.project import initialize_project
from wmb.core.state_store import IllegalTransition, StateStore


def test_state_store_appends_event_for_legal_transition(tmp_path):
    project = initialize_project(tmp_path)
    store = StateStore(project)
    event = store.transition(
        actor="orchestrator",
        to_status="awaiting_research_direction",
        decision="PROCEED",
        reason="data contract reconciled",
    )
    assert event["from_status"] == "intake"
    assert store.load_run()["status"] == "awaiting_research_direction"


def test_illegal_transition_is_rejected(tmp_path):
    store = StateStore(initialize_project(tmp_path))
    with pytest.raises(IllegalTransition):
        store.transition(
            actor="worker",
            to_status="candidate_level_4",
            decision="PROCEED",
            reason="worker tried to skip gates",
        )
```

- [ ] **Step 2: Run and verify failure**

Run: `python -m pytest tests/test_state_store.py -q`  
Expected: FAIL because the state store does not exist.

- [ ] **Step 3: Implement legal transitions and state writes**

Define explicit legal transitions between:

```text
intake
awaiting_research_direction
evidence_and_analysis
result_and_claim_build
manuscript_drafting
independent_review
package_verification
awaiting_final_confirmation
candidate_level_4
downgraded
blocked
```

Only `actor="orchestrator"` may call `transition`. Validate the projected run
before atomically replacing `run.yaml`, then append the validated event to
`events.jsonl`. Every `BLOCK` transition requires `unblock_conditions`; every
`DOWNGRADE` transition requires `deliverable`.

- [ ] **Step 4: Run tests**

Run: `python -m pytest tests/test_state_store.py -q`  
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add wmb/core/state_machine.py wmb/core/state_store.py tests/test_state_store.py
git commit -m "feat: enforce legal workflow transitions"
```

## Task 4: Task Contracts, Dynamic Routing, and Isolation

**Files:**
- Create: `wmb/core/task_router.py`
- Test: `tests/test_task_router.py`

- [ ] **Step 1: Write failing routing and isolation tests**

```python
from wmb.core.project import initialize_project
from wmb.core.task_router import TaskRouter


def test_router_selects_dynamic_ecology_capabilities(tmp_path):
    router = TaskRouter(initialize_project(tmp_path))
    capabilities = router.select_capabilities(
        data_types=["camera_trap"],
        methods=["occupancy"],
        risks=["sensitive_location"],
        stage="evidence_and_analysis",
    )
    assert "occupancy_statistician" in capabilities
    assert "camera_trap_ecologist" in capabilities
    assert "sensitive_location_reviewer" in capabilities


def test_reviewer_cannot_share_writer_context(tmp_path):
    router = TaskRouter(initialize_project(tmp_path))
    writer = router.create_task("manuscript_writer", "Draft Results", [], ["draft.md"])
    reviewer = router.create_task(
        "statistical_reviewer",
        "Review Results",
        ["draft.md"],
        ["review.yaml"],
        review_of=writer["task_id"],
    )
    assert reviewer["context_id"] != writer["context_id"]
    assert reviewer["role"] == "reviewer"
```

- [ ] **Step 2: Run and verify failure**

Run: `python -m pytest tests/test_task_router.py -q`  
Expected: FAIL because the router does not exist.

- [ ] **Step 3: Implement router**

Implement deterministic capability rules for the existing WMB data types and
methods, with additive generic writer/reviewer capabilities. `create_task`
must emit and validate a task contract, persist it under `.wmb/tasks/`, and
assign a new context ID to reviewers.

Reject reviewer tasks whose declared context matches the worker task or whose
allowed inputs include unlisted restricted artifacts.

- [ ] **Step 4: Run tests**

Run: `python -m pytest tests/test_task_router.py -q`  
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add wmb/core/task_router.py tests/test_task_router.py
git commit -m "feat: route dynamic isolated agent tasks"
```

## Task 5: Gate Engine and Author Confirmation Queue

**Files:**
- Create: `wmb/core/gate_engine.py`
- Test: `tests/test_gate_engine.py`

- [ ] **Step 1: Write failing Gate-policy tests**

```python
from wmb.core.gate_engine import GateEngine
from wmb.core.project import initialize_project


def test_major_analysis_change_requires_author_confirmation(tmp_path):
    engine = GateEngine(initialize_project(tmp_path))
    decision = engine.evaluate_change(
        {
            "change_type": "response_variable",
            "summary": "replace occupancy with abundance",
        }
    )
    assert decision.status == "awaiting_author_confirmation"


def test_low_risk_claim_narrowing_can_auto_refine(tmp_path):
    engine = GateEngine(initialize_project(tmp_path))
    decision = engine.evaluate_change(
        {"change_type": "claim_narrowing", "summary": "replace causes with associated"}
    )
    assert decision.status == "auto_refine"
```

- [ ] **Step 2: Run and verify failure**

Run: `python -m pytest tests/test_gate_engine.py -q`  
Expected: FAIL because the Gate engine does not exist.

- [ ] **Step 3: Implement Gate policy**

Implement explicit major-change categories:

```text
research_question
core_hypothesis
response_variable
core_model
inferential_target
key_sample_exclusion
key_inclusion_criteria
unsupported_research_direction
final_submission_package
authorship_or_declarations
```

Major changes append a unique pending item to
`author_confirmation_queue.yaml`. Low-risk categories return `auto_refine`.
Unknown categories return a blocking decision rather than guessing.

- [ ] **Step 4: Run tests**

Run: `python -m pytest tests/test_gate_engine.py -q`  
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add wmb/core/gate_engine.py tests/test_gate_engine.py
git commit -m "feat: enforce author confirmation gates"
```

## Task 6: Finite Loops and No-Silent-Skip Ledger

**Files:**
- Create: `wmb/core/loop_controller.py`
- Create: `wmb/core/logging.py`
- Test: `tests/test_loop_controller.py`
- Test: `tests/test_rejection_log.py`

- [ ] **Step 1: Write failing loop tests**

```python
from wmb.core.loop_controller import LoopController


def test_loop_stops_after_three_rounds():
    controller = LoopController(max_rounds=3)
    assert controller.evaluate(1, ["I1"], ["I1"], 0).action == "REFINE"
    assert controller.evaluate(2, ["I1"], ["I1"], 0).action == "BLOCK"


def test_loop_stops_early_when_gate_passes():
    controller = LoopController(max_rounds=3)
    assert controller.evaluate(1, ["I1"], [], 1).action == "PROCEED"
```

The first test encodes the stricter rule that the same blocking issue failing
to improve for two consecutive rounds blocks before the absolute three-round
limit.

- [ ] **Step 2: Write failing rejection-ledger test**

```python
import json

from wmb.core.logging import RejectionLedger
from wmb.core.project import initialize_project


def test_rejection_ledger_records_skips(tmp_path):
    ledger = RejectionLedger(initialize_project(tmp_path))
    ledger.record("source", "paper-17", "duplicate DOI", action="skipped")
    entry = json.loads(ledger.path.read_text("utf-8").splitlines()[0])
    assert entry["reason"] == "duplicate DOI"
```

- [ ] **Step 3: Run and verify failure**

Run: `python -m pytest tests/test_loop_controller.py tests/test_rejection_log.py -q`  
Expected: FAIL because the modules do not exist.

- [ ] **Step 4: Implement loop and ledger**

`LoopController.evaluate` must consider Gate pass, resolved blocker count,
severity reduction, evidence-trace coverage increase, repeated blockers,
round limit, and author-confirmation triggers. Language-only changes do not
count as material improvement.

`RejectionLedger` appends JSONL entries for failures, skips, exclusions,
retries, dropped claims, and rejected sources.

- [ ] **Step 5: Run tests and commit**

Run: `python -m pytest tests/test_loop_controller.py tests/test_rejection_log.py -q`  
Expected: PASS.

```bash
git add wmb/core/loop_controller.py wmb/core/logging.py tests
git commit -m "feat: add finite revision loops and rejection ledger"
```

## Task 7: Analysis Provenance and Claim Trace

**Files:**
- Create: `wmb/core/provenance.py`
- Test: `tests/test_provenance.py`

- [ ] **Step 1: Write failing provenance tests**

```python
import pytest

from wmb.core.provenance import ProvenanceError, ProvenanceStore
from wmb.core.project import initialize_project


def test_failed_analysis_cannot_support_claim(tmp_path):
    store = ProvenanceStore(initialize_project(tmp_path))
    store.record_analysis(
        {
            "analysis_id": "A1",
            "status": "failed",
            "command": "Rscript occupancy.R",
            "input_hashes": {"data.csv": "sha256:x"},
            "outputs": [],
            "warnings": [],
            "errors": ["convergence failed"],
            "exclusions": [],
            "limitations": [],
        }
    )
    with pytest.raises(ProvenanceError):
        store.record_claim_trace(
            claim_id="C1",
            analysis_id="A1",
            result_card="R1",
            manuscript_claim="occupancy increased",
        )
```

- [ ] **Step 2: Run and verify failure**

Run: `python -m pytest tests/test_provenance.py -q`  
Expected: FAIL because provenance support does not exist.

- [ ] **Step 3: Implement provenance**

Persist validated analysis records under `.wmb/artifacts/analysis/` and claim
traces under `.wmb/artifacts/claims/`. Require successful or
`usable_with_caveat` analysis status for a supporting trace. Validate that all
referenced files exist and hashes match when present.

- [ ] **Step 4: Run tests and commit**

Run: `python -m pytest tests/test_provenance.py -q`  
Expected: PASS.

```bash
git add wmb/core/provenance.py tests/test_provenance.py
git commit -m "feat: trace analyses to manuscript claims"
```

## Task 8: Journal Contract and Submission Verifier

**Files:**
- Create: `wmb/core/journal.py`
- Create: `wmb/core/verifier.py`
- Test: `tests/test_journal.py`
- Test: `tests/test_verifier.py`

- [ ] **Step 1: Write failing journal and verifier tests**

```python
from wmb.core.journal import DEFAULT_JOURNAL_URL, default_contract
from wmb.core.verifier import PackageVerifier


def test_default_journal_contract_is_biodiversity_science():
    contract = default_contract()
    assert contract["journal_name"] == "生物多样性"
    assert contract["source_url"] == DEFAULT_JOURNAL_URL
    assert set(contract["bilingual_elements"]) == {"title", "abstract", "keywords"}


def test_placeholder_author_deterministically_blocks_level_4(tmp_path):
    report = PackageVerifier(tmp_path).verify(
        author={"display_name": "Dr. Who", "status": "placeholder"},
        package={"sections": ["title", "abstract", "methods", "results", "discussion"]},
    )
    assert any(f.code == "AUTHOR_PLACEHOLDER" and f.blocking for f in report.findings)


def test_heuristic_finding_never_blocks(tmp_path):
    report = PackageVerifier(tmp_path).verify(
        author={"display_name": "Real Author", "status": "confirmed"},
        package={"sections": ["title"], "discussion_strength": "possibly_weak"},
    )
    assert all(not f.blocking for f in report.findings if f.kind == "heuristic")
```

- [ ] **Step 2: Run and verify failure**

Run: `python -m pytest tests/test_journal.py tests/test_verifier.py -q`  
Expected: FAIL because journal and verifier modules do not exist.

- [ ] **Step 3: Implement contract refresh and verifier**

Set:

```python
DEFAULT_JOURNAL_URL = "https://www.biodiversity-science.net/CN/column/column49.shtml"
```

`refresh_contract` fetches official HTML with a timeout, stores retrieval time
and SHA-256 hash, and marks the contract `fresh`. On failure it preserves the
cached contract and marks it `stale`.

The verifier returns structured deterministic and heuristic findings.
Deterministic checks cover required bilingual elements, citation/reference
set mismatch, missing central traces, sensitive data findings, and author or
declaration placeholders. Heuristic checks never set `blocking=True`.

- [ ] **Step 4: Run tests and commit**

Run: `python -m pytest tests/test_journal.py tests/test_verifier.py -q`  
Expected: PASS.

```bash
git add wmb/core/journal.py wmb/core/verifier.py tests
git commit -m "feat: verify journal submission packages"
```

## Task 9: Recovery and Consistency

**Files:**
- Create: `wmb/core/recovery.py`
- Test: `tests/test_recovery.py`

- [ ] **Step 1: Write failing recovery tests**

```python
from wmb.core.project import initialize_project
from wmb.core.recovery import RecoveryManager


def test_recovery_marks_running_task_without_output_retryable(tmp_path):
    project = initialize_project(tmp_path)
    task = project.wmb_dir / "tasks" / "T1.yaml"
    task.write_text(
        "task_id: T1\ncapability: writer\nobjective: draft\n"
        "allowed_inputs: []\nrequired_outputs: [missing.md]\n"
        "acceptance_criteria: [complete]\nprohibited_actions: []\n"
        "max_attempts: 3\nstatus: running\n",
        encoding="utf-8",
    )
    report = RecoveryManager(project).recover()
    assert "T1" in report.retryable_tasks


def test_recovery_does_not_rerun_completed_unchanged_task(tmp_path):
    project = initialize_project(tmp_path)
    output = tmp_path / "draft.md"
    output.write_text("completed manuscript artifact", encoding="utf-8")
    task = project.wmb_dir / "tasks" / "T2.yaml"
    task.write_text(
        "task_id: T2\ncapability: writer\nobjective: draft\n"
        "allowed_inputs: []\nrequired_outputs: [draft.md]\n"
        "acceptance_criteria: [complete]\nprohibited_actions: []\n"
        "max_attempts: 3\nstatus: completed\n",
        encoding="utf-8",
    )
    report = RecoveryManager(project).recover()
    assert report.tasks_to_rerun == []
```

- [ ] **Step 2: Run and verify failure**

Run: `python -m pytest tests/test_recovery.py -q`  
Expected: FAIL because recovery support does not exist.

- [ ] **Step 3: Implement recovery**

Recovery validates all canonical records, checks event order and artifact
hashes, identifies retryable running tasks, skips unchanged completed tasks,
and reports adapter-state mismatches. Corrupt canonical state raises
`RecoveryBlocked`; it never guesses or rewrites scientific decisions.

- [ ] **Step 4: Run tests and commit**

Run: `python -m pytest tests/test_recovery.py -q`  
Expected: PASS.

```bash
git add wmb/core/recovery.py tests/test_recovery.py
git commit -m "feat: recover interrupted manuscript runs"
```

## Task 10: Adapter Protocol and Codex Adapter

**Files:**
- Create: `wmb/adapters/base.py`
- Create: `wmb/adapters/codex.py`
- Test: `tests/test_codex_adapter.py`

- [ ] **Step 1: Write failing Codex adapter test**

```python
from wmb.adapters.codex import CodexAdapter
from wmb.core.project import initialize_project
from wmb.core.task_router import TaskRouter


def test_codex_adapter_emits_executable_dispatch_packet(tmp_path):
    project = initialize_project(tmp_path)
    task = TaskRouter(project).create_task("manuscript_writer", "Draft", [], ["draft.md"])
    packet = CodexAdapter(project).prepare_dispatch(task)
    assert packet["adapter"] == "codex"
    assert packet["operation"] == "spawn_agent"
    assert packet["task_contract_path"].endswith(f"{task['task_id']}.yaml")
    assert packet["result_contract_path"].endswith(f"{task['task_id']}.result.yaml")
```

- [ ] **Step 2: Run and verify failure**

Run: `python -m pytest tests/test_codex_adapter.py -q`  
Expected: FAIL because adapters do not exist.

- [ ] **Step 3: Implement base and Codex adapter**

Define an adapter protocol with `prepare_dispatch`, `ingest_result`, and
`reconcile`. The Codex adapter emits a complete dispatch packet consumed by
the active Codex agent, including task path, isolated-context requirement,
expected result path, and result schema. `ingest_result` validates the result
and updates only task execution status; canonical Gate decisions remain in
the core.

- [ ] **Step 4: Run tests and commit**

Run: `python -m pytest tests/test_codex_adapter.py -q`  
Expected: PASS.

```bash
git add wmb/adapters tests/test_codex_adapter.py
git commit -m "feat: add executable Codex task adapter"
```

## Task 11: Hermes Durable Adapter

**Files:**
- Create: `wmb/adapters/hermes.py`
- Test: `tests/test_hermes_adapter.py`

- [ ] **Step 1: Write failing Hermes mapping tests**

```python
from wmb.adapters.hermes import HermesAdapter
from wmb.core.project import initialize_project
from wmb.core.task_router import TaskRouter


def test_hermes_adapter_maps_durable_task_and_dependencies(tmp_path):
    project = initialize_project(tmp_path)
    task = TaskRouter(project).create_task("statistical_reviewer", "Review", [], ["review.yaml"])
    command = HermesAdapter(project, executable="hermes").build_create_command(
        task, dependencies=["analysis-001"]
    )
    joined = " ".join(command)
    assert "kanban" in joined
    assert task["task_id"] in joined
    assert "analysis-001" in joined
```

- [ ] **Step 2: Run and verify failure**

Run: `python -m pytest tests/test_hermes_adapter.py -q`  
Expected: FAIL because the Hermes adapter does not exist.

- [ ] **Step 3: Inspect installed Hermes command syntax**

Run:

```powershell
hermes kanban --help
hermes kanban task --help
```

Expected: command help showing the installed Durable Kanban interface. Use the
actual installed syntax in the adapter and tests.

- [ ] **Step 4: Implement Hermes adapter**

Implement safe argument-list command construction, optional subprocess
execution, task dependency/profile mapping, result ingestion, and reconciliation.
Do not use shell-built command strings. Use Durable Kanban for durable tasks;
mark `delegate_task` as permitted only for non-durable exploratory subtasks.

- [ ] **Step 5: Run tests and commit**

Run: `python -m pytest tests/test_hermes_adapter.py -q`  
Expected: PASS.

```bash
git add wmb/adapters/hermes.py tests/test_hermes_adapter.py
git commit -m "feat: add Hermes durable workflow adapter"
```

## Task 12: CLI and Cross-Platform Conformance

**Files:**
- Create: `wmb/cli.py`
- Create: `wmb/__main__.py`
- Create: `tests/conftest.py`
- Create: `tests/fixtures/basic_project/project.yaml`
- Create: `tests/test_cli.py`
- Create: `tests/test_adapter_conformance.py`

- [ ] **Step 1: Write failing CLI and conformance tests**

```python
from wmb.cli import main


def test_cli_init_and_status(tmp_path, capsys):
    assert main(["init", str(tmp_path)]) == 0
    assert main(["status", str(tmp_path)]) == 0
    assert "生物多样性" in capsys.readouterr().out
```

```python
from wmb.adapters.codex import CodexAdapter
from wmb.adapters.hermes import HermesAdapter


def test_adapters_do_not_change_core_gate_decision(basic_project, validated_result):
    codex = CodexAdapter(basic_project).ingest_result(validated_result)
    hermes = HermesAdapter(basic_project).ingest_result(validated_result)
    assert codex.recommended_transition == hermes.recommended_transition
```

- [ ] **Step 2: Run and verify failure**

Run: `python -m pytest tests/test_cli.py tests/test_adapter_conformance.py -q`  
Expected: FAIL because CLI and fixtures do not exist.

- [ ] **Step 3: Implement CLI**

Provide:

```text
wmb init PROJECT
wmb status PROJECT
wmb task create PROJECT --capability ... --objective ...
wmb result ingest PROJECT RESULT
wmb transition PROJECT --to ... --decision ... --reason ...
wmb resume PROJECT
wmb verify PROJECT
wmb dispatch PROJECT TASK_ID --platform codex|hermes
wmb journal refresh PROJECT
```

Commands print concise YAML or JSON summaries and return non-zero on blocking
validation errors.

- [ ] **Step 4: Add conformance fixture and run tests**

Run: `python -m pytest tests/test_cli.py tests/test_adapter_conformance.py -q`  
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add wmb tests/test_cli.py tests/test_adapter_conformance.py tests/fixtures pyproject.toml
git commit -m "feat: add WMB CLI and adapter conformance"
```

## Task 13: Repair References and Update Skill Instructions

**Files:**
- Create: `references/rewriting-existing-manuscript.md`
- Create: `references/literature-search-fallback.md`
- Create: `references/multi-agent-workflow.md`
- Modify: `references/run-lessons.md`
- Modify: `references/journal-target-contract.md`
- Modify: `SKILL.md`
- Test: `tests/test_skill_references.py`

- [ ] **Step 1: Write failing reference-integrity test**

```python
import re
from pathlib import Path


def test_all_local_reference_links_exist():
    root = Path(__file__).parents[1]
    text = (root / "SKILL.md").read_text("utf-8")
    links = re.findall(r"`(references/[^`]+\.md)`", text)
    missing = [link for link in links if not (root / link).exists()]
    assert missing == []
```

- [ ] **Step 2: Run and verify failure**

Run: `python -m pytest tests/test_skill_references.py -q`  
Expected: FAIL with the two currently missing reference files.

- [ ] **Step 3: Write operator documentation**

Update `SKILL.md` to route multi-agent builds through
`references/multi-agent-workflow.md`, document `.wmb/` as source of truth,
state the three scientific/final confirmation moments plus metadata
confirmation, and document default `Dr. Who` and 《生物多样性》 behavior.

The literature fallback reference must never embed API keys or secret paths.
The run-lessons reference must require capture, author approval, versioned
publication, and explicit project enablement. Remove automatic Hermes skill
injection.

- [ ] **Step 4: Run reference test and commit**

Run: `python -m pytest tests/test_skill_references.py -q`  
Expected: PASS.

```bash
git add SKILL.md references tests/test_skill_references.py
git commit -m "docs: document executable multi-agent workflow"
```

## Task 14: End-to-End Acceptance and Full Verification

**Files:**
- Create: `tests/test_end_to_end.py`
- Modify: files identified by failing acceptance tests only.

- [ ] **Step 1: Write end-to-end acceptance test**

```python
from wmb.adapters.codex import CodexAdapter
from wmb.adapters.hermes import HermesAdapter
from wmb.core.gate_engine import GateEngine
from wmb.core.project import initialize_project
from wmb.core.recovery import RecoveryManager
from wmb.core.verifier import PackageVerifier


def test_cross_platform_run_stops_at_level_3_with_placeholder_author(tmp_path):
    project = initialize_project(tmp_path)
    assert GateEngine(project).evaluate_change(
        {"change_type": "claim_narrowing", "summary": "narrow claim"}
    ).status == "auto_refine"
    assert CodexAdapter(project).adapter_name == "codex"
    assert HermesAdapter(project, executable="hermes").adapter_name == "hermes"
    assert RecoveryManager(project).recover().blocked is False
    report = PackageVerifier(tmp_path).verify(
        author={"display_name": "Dr. Who", "status": "placeholder"},
        package={"sections": ["title", "abstract", "methods", "results", "discussion"]},
    )
    assert report.maximum_level == 3
```

- [ ] **Step 2: Run full suite**

Run: `python -m pytest -q`  
Expected: all tests pass.

- [ ] **Step 3: Run CLI smoke test**

Run:

```powershell
$project = Join-Path $env:TEMP 'wmb-smoke'
python -m wmb init $project
python -m wmb status $project
python -m wmb verify $project
```

Expected: initialization and status succeed; verification reports Level 3 or
lower because `Dr. Who` and author declarations remain unconfirmed.

- [ ] **Step 4: Run quality checks**

Run:

```powershell
git diff --check
python -m pytest -q
git status --short
```

Expected: no whitespace errors, all tests pass, and only intended files are
modified.

- [ ] **Step 5: Commit final acceptance coverage**

```bash
git add tests/test_end_to_end.py
git commit -m "test: cover cross-platform manuscript workflow"
```

## Final Acceptance Checklist

- [ ] `.wmb/` is the sole canonical state source.
- [ ] Only the state store can perform legal transitions.
- [ ] Worker and reviewer contexts are isolated.
- [ ] Major analysis changes request author confirmation.
- [ ] Low-risk changes loop automatically and finitely.
- [ ] Analysis, claims, result cards, and captions can be traced.
- [ ] Failures, exclusions, retries, and skips are recorded.
- [ ] Deterministic package failures block; heuristics only warn.
- [ ] `Dr. Who` prevents Level 4 until confirmed.
- [ ] 《生物多样性》 is the default journal with stale-cache behavior.
- [ ] Codex and Hermes adapters preserve identical core Gate policy.
- [ ] Interrupted work resumes without duplicating unchanged completed tasks.
- [ ] Missing references are repaired and operator instructions are current.
- [ ] `python -m pytest -q` passes.
