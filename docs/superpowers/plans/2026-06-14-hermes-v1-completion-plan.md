# WMB V1 Hermes Completion Plan

> **For Hermes workers:** Execute this plan through Durable Kanban as ten serial cards, H0 through H9. Use the existing `feat/multi-agent-workflow` branch and shared repository directory. Never run two writer cards concurrently. Do not merge to `main`.

**Goal:** Complete the usable V1 workflow from the current Task 1-4 foundation, prioritizing a working Hermes vertical slice before secondary scientific traceability and documentation.

**Architecture:** Keep the existing `.wmb/` state store, legal state machine, contract schemas, and task router unchanged unless a new end-to-end test demonstrates a blocking defect. Add small, focused modules for Gates, loops, adapters, recovery, provenance, journal verification, CLI integration, and documentation. Both Codex and Hermes adapters consume the same core decisions and never implement independent Gate policy.

**Tech Stack:** Python 3.11, standard library, PyYAML, jsonschema, pytest, Hermes Durable Kanban v0.16.0.

---

## 1. Current Baseline

Repository:

```text
C:\Users\Administrator\.codex\skills\wildlife-manuscript-builder
```

Required branch:

```text
feat/multi-agent-workflow
```

Baseline when this plan was written:

```text
HEAD: 80cb68b
origin/main: 32bac58
Tests: 363 passed
Working tree: clean
```

Already implemented and protected from unrelated refactoring:

- contract schemas and validation;
- `.wmb/` project initialization;
- default `Dr. Who` placeholder;
- default 《生物多样性》 contract;
- legal state machine and single state writer;
- event audit and transaction recovery;
- dynamic task routing;
- Worker/Reviewer isolation;
- restricted-artifact registry and authorization.

Missing:

- Gate Engine and author-confirmation queue behavior;
- finite revision loops and rejection ledger;
- Codex and Hermes adapters;
- working workflow CLI;
- general recovery manager;
- analysis and claim provenance;
- journal refresh and package verifier;
- operator documentation and end-to-end acceptance.

## 2. Execution Rules

These rules override the older implementation plan where they differ.

### 2.1 End-to-end first

The first usable vertical slice must exist after H3:

```text
initialize project
→ create task
→ prepare Hermes dispatch
→ ingest structured result
→ evaluate Gate/loop decision
→ inspect status
```

Do not postpone CLI and Hermes execution until every secondary module is
perfect.

### 2.2 Scope control

- Do not redesign Task 1-4 foundations.
- Do not add a new database.
- Do not implement V2 patch revision, cross-model audits, or gold-set
  calibration.
- Do not add new security hardening unless a planned acceptance test fails.
- Keep each production module below roughly 500 lines. Split by responsibility
  before exceeding that size.
- Do not expand a card after its stated acceptance tests pass.
- Record non-blocking improvement ideas as a Kanban comment beginning with
  `DEFERRED:` and continue.

### 2.3 Review budget

Each card receives:

1. implementation and self-review;
2. one specification review;
3. one code-quality review;
4. at most one repair round for material findings.

After that repair round, remaining non-blocking findings become `DEFERRED:`
comments. A finding blocks only if it breaks a listed acceptance behavior,
causes data loss, violates author confirmation, leaks restricted material, or
allows false Level 4 status.

### 2.4 Card completion protocol

Every card must:

1. start from a clean working tree;
2. run its targeted test and confirm the new test fails before implementation;
3. implement only owned files;
4. run targeted tests;
5. run `python -m pytest -q`;
6. run `git diff --check`;
7. commit using the specified message;
8. push `feat/multi-agent-workflow` to `origin`;
9. complete the Kanban card with:
   - commit SHA;
   - files changed;
   - targeted test count;
   - full test count;
   - deferred findings.

If tests fail outside the card's owned files, the card may fix only direct
integration fallout caused by its changes. Otherwise block with the exact
failure output.

### 2.5 Recovery after interruption

At the beginning of every resumed card:

```powershell
git switch feat/multi-agent-workflow
git status --short --branch
git log -1 --oneline
python -m pytest -q
```

Then inspect the card's latest run and comments:

```powershell
hermes kanban runs TASK_ID
hermes kanban show TASK_ID
```

Resume from the last committed step. Never repeat a completed card. Never
discard unrecognized changes; block and report them.

## 3. Durable Card Graph

Run all cards serially in this dependency order:

```text
H0 Baseline and remote checkpoint
  → H1 Gate engine, finite loop, rejection ledger
  → H2 Adapter protocol, Hermes adapter, Codex adapter
  → H3 Minimal CLI and first executable vertical slice
  → H4 Recovery manager
  → H5 Analysis provenance and claim trace
  → H6 Journal refresh and submission verifier
  → H7 Final CLI, adapter parity, and end-to-end workflow
  → H8 Skill and operator documentation
  → H9 Final acceptance and GitHub checkpoint
```

Use these Kanban settings for H1-H8:

```text
assignee: default
workspace: dir:C:\Users\Administrator\.codex\skills\wildlife-manuscript-builder
branch: feat/multi-agent-workflow
max-runtime: 2h
max-retries: 2
goal: enabled
goal-max-turns: 8
```

H0 and H9 may use a 1h runtime. Dispatch at most one worker:

```powershell
hermes kanban dispatch --max 1 --failure-limit 2
```

## 4. H0: Baseline and Remote Checkpoint

**Purpose:** Ensure Hermes starts from the reviewed baseline and the feature
branch exists on GitHub before further work.

**Owned files:** None.

**Steps:**

1. Verify repository and branch:

```powershell
git switch feat/multi-agent-workflow
git status --short --branch
git log -1 --oneline
git fetch origin
```

Expected:

```text
clean working tree
HEAD includes 80cb68b or a direct descendant
```

2. Run baseline:

```powershell
python -m pytest -q
git diff --check
```

Expected:

```text
363 or more tests pass
no whitespace errors in files changed after this plan
```

The existing design and older plan contain historical Markdown trailing spaces;
do not rewrite those documents merely to silence `git diff --check
origin/main...HEAD`.

3. Publish the feature branch:

```powershell
git push -u origin feat/multi-agent-workflow
```

4. Confirm remote checkpoint:

```powershell
git ls-remote --heads origin feat/multi-agent-workflow
```

**Acceptance:**

- baseline tests pass;
- local tree is clean;
- remote feature branch points to current HEAD.

**Commit:** No new commit required.

## 5. H1: Gate Engine, Finite Loop, and Rejection Ledger

**Dependency:** H0.

**Owned files:**

- Create `wmb/core/gate_engine.py`
- Create `wmb/core/loop_controller.py`
- Create `wmb/core/logging.py`
- Create `tests/test_gate_engine.py`
- Create `tests/test_loop_controller.py`
- Create `tests/test_rejection_log.py`

### Required API

`GateEngine(project).evaluate_change(change)` returns an immutable decision
with:

```text
status
change_type
summary
queue_item_id
reason
```

Major categories:

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

These return `awaiting_author_confirmation` and append one idempotent pending
item to `author_confirmation_queue.yaml`.

Low-risk categories:

```text
claim_narrowing
citation_sync
figure_table_sync
method_description
language_structure
format_repair
```

These return `auto_refine` without changing canonical workflow state.

Unknown categories return `blocked_unknown_change`. Never guess.

`LoopController(max_rounds=3).evaluate(...)` returns:

```text
PROCEED
REFINE
BLOCK
AUTHOR_CONFIRMATION
```

Rules:

- Gate pass → `PROCEED`;
- author trigger → `AUTHOR_CONFIRMATION`;
- same blocking issue unchanged for two rounds → `BLOCK`;
- round 3 without pass → `BLOCK`;
- resolved blocker, reduced severity, or increased trace coverage → material
  improvement;
- language-only edits are not material improvement.

`RejectionLedger(project).record(...)` appends valid JSONL to
`.wmb/logs/rejections.jsonl` for:

```text
failed
skipped
excluded
retried
dropped_claim
rejected_source
```

### Required tests

- major analysis change creates exactly one pending confirmation;
- repeated identical major change does not duplicate queue item;
- low-risk claim narrowing auto-refines;
- unknown change blocks;
- queue write failure does not produce partial/corrupt YAML;
- loop proceeds when blockers are resolved;
- loop blocks after the same blocker fails twice;
- loop blocks at round three;
- author trigger interrupts loop;
- ledger records all allowed actions and rejects blank reasons;
- concurrent ledger appends remain valid JSONL.

### Verification

```powershell
python -m pytest tests/test_gate_engine.py tests/test_loop_controller.py tests/test_rejection_log.py -q
python -m pytest -q
git diff --check
```

**Commit:**

```text
feat: add author gates and finite revision loops
```

## 6. H2: Adapter Protocol, Hermes Adapter, and Codex Adapter

**Dependency:** H1.

**Owned files:**

- Create `wmb/adapters/base.py`
- Create `wmb/adapters/codex.py`
- Create `wmb/adapters/hermes.py`
- Create `tests/test_codex_adapter.py`
- Create `tests/test_hermes_adapter.py`

### Shared adapter contract

Both adapters expose:

```text
adapter_name
prepare_dispatch(task, dependencies=[])
ingest_result(result)
reconcile()
```

Adapters may update task execution status, but must not call
`StateStore.transition()` or decide a Gate.

### Codex adapter

`prepare_dispatch` returns a structured packet containing:

```text
adapter: codex
operation: spawn_agent
task_contract_path
result_contract_path
isolated_context: true for reviewers
capability
objective
allowed_inputs
required_outputs
```

It does not attempt to invoke Codex tools from Python.

### Hermes adapter

Use the installed Hermes v0.16.0 syntax:

```text
hermes kanban create TITLE --body BODY --workspace dir:PROJECT
  --idempotency-key TASK_ID --max-runtime 2h --max-retries 2 --json
```

Dependencies map to repeated `--parent PARENT_ID`.

Profiles map from capability through a small explicit dictionary with
`default` fallback.

Required methods:

```text
build_create_command(task, dependencies=[])
execute_dispatch(task, dependencies=[], runner=subprocess.run)
ingest_result(result)
reconcile()
```

Command construction must use an argument list. Never construct a shell
string. Tests inject a fake runner and do not create real Kanban tasks.

The task body must contain:

- canonical task-contract path;
- expected result-contract path;
- instruction to write structured result;
- instruction not to change `.wmb/run.yaml`;
- instruction to stop on prohibited action.

### Required tests

- Codex packet contains complete paths and isolation metadata;
- Hermes command uses `kanban create`, never nonexistent `kanban task`;
- dependencies become `--parent`;
- task ID becomes idempotency key;
- no shell string is used;
- invalid result fails contract validation;
- accepted result updates only task execution status;
- neither adapter changes Gate/canonical run state;
- reconciling the same result is idempotent.

### Verification

```powershell
python -m pytest tests/test_codex_adapter.py tests/test_hermes_adapter.py -q
python -m pytest -q
git diff --check
```

**Commit:**

```text
feat: add Codex and Hermes task adapters
```

## 7. H3: Minimal CLI and First Executable Vertical Slice

**Dependency:** H2.

**Owned files:**

- Modify `wmb/cli.py`
- Create `wmb/__main__.py`
- Modify `tests/test_cli.py`
- Create `tests/test_vertical_slice.py`

### Required CLI commands

Implement only these commands in H3:

```text
wmb init PROJECT
wmb status PROJECT
wmb task create PROJECT --capability CAPABILITY --objective OBJECTIVE
  [--input PATH] [--output PATH]
wmb dispatch PROJECT TASK_ID --platform codex|hermes
wmb result ingest PROJECT RESULT_FILE --platform codex|hermes
wmb change evaluate PROJECT CHANGE_FILE
```

All commands:

- print JSON to stdout;
- print errors to stderr;
- return `0` on success;
- return `2` on invalid input/contract;
- return `3` when author confirmation or a block is required.

`wmb dispatch --platform hermes` prints the safe Hermes command by default.
It executes it only with explicit `--execute`.

### Vertical-slice test

The test must perform:

```text
initialize project
→ create manuscript_writer task
→ prepare Hermes command without execution
→ write valid structured result
→ ingest result
→ evaluate low-risk claim narrowing
→ confirm canonical run remains controlled by StateStore
```

Also test:

```text
python -m wmb --help
python -m wmb init ...
wmb init ...
```

### Verification

```powershell
python -m pytest tests/test_cli.py tests/test_vertical_slice.py -q
python -m pytest -q

$smoke = Join-Path $env:TEMP 'wmb-h3-smoke'
python -m wmb init $smoke
python -m wmb status $smoke
```

Expected: init and status succeed and status output includes `生物多样性`,
`Dr. Who`, `intake`, and `data_contract`.

**Commit:**

```text
feat: add executable WMB vertical slice
```

**Milestone:** After H3, WMB must be usable for durable Hermes task dispatch
and structured result ingestion. Do not continue if this milestone fails.

## 8. H4: Recovery Manager

**Dependency:** H3.

**Owned files:**

- Create `wmb/core/recovery.py`
- Create `tests/test_recovery.py`

### Required API

`RecoveryManager(project).recover(adapter_state=None)` returns:

```text
blocked
retryable_tasks
tasks_to_rerun
unchanged_completed_tasks
adapter_mismatches
issues
```

Required behavior:

- validate canonical run and event audit;
- validate every task contract;
- running task without valid required outputs → retryable;
- completed task with unchanged valid outputs → do not rerun;
- completed task with missing/changed outputs → block, do not silently rerun;
- detect adapter state mismatch without changing scientific state;
- corrupt canonical state raises `RecoveryBlocked`;
- never invent a Gate decision.

Use existing task/artifact canonicalization. Do not build a second recovery
transaction system.

### Required tests

- interrupted running task becomes retryable;
- unchanged completed task is skipped;
- changed completed artifact blocks;
- corrupt run/event/task blocks;
- adapter mismatch is reported;
- repeated recovery is idempotent.

### Verification

```powershell
python -m pytest tests/test_recovery.py -q
python -m pytest -q
git diff --check
```

**Commit:**

```text
feat: recover interrupted manuscript runs
```

## 9. H5: Analysis Provenance and Claim Trace

**Dependency:** H4.

**Owned files:**

- Create `wmb/core/provenance.py`
- Create `tests/test_provenance.py`

### Required API

`ProvenanceStore(project)` provides:

```text
record_analysis(payload)
record_claim_trace(...)
validate_claim_trace(claim_id)
validate_all_central_claims()
```

Persist:

```text
.wmb/artifacts/analysis/ANALYSIS_ID.yaml
.wmb/artifacts/claims/CLAIM_ID.yaml
```

Claim trace fields:

```text
claim_id
central
analysis_id or evidence_source
result_card
manuscript_claim
figure_or_table_caption
status
```

Rules:

- failed analysis cannot support a claim;
- only `successful` and `usable_with_caveat` analysis can support a claim;
- referenced files must exist;
- declared hashes must match;
- every central claim requires a result card and emitted manuscript claim;
- central figure/table caption requires a central claim trace;
- persistence is no-clobber and idempotent for identical records.

### Required tests

- failed analysis rejected as evidence;
- valid analysis supports claim;
- hash mismatch blocks;
- missing result card blocks central claim;
- missing caption trace blocks central figure/table claim;
- non-central narrative claim may omit figure caption;
- repeated identical record is idempotent.

### Verification

```powershell
python -m pytest tests/test_provenance.py -q
python -m pytest -q
git diff --check
```

**Commit:**

```text
feat: trace analyses to manuscript claims
```

## 10. H6: Journal Refresh and Submission Verifier

**Dependency:** H5.

**Owned files:**

- Create `wmb/core/journal.py`
- Create `wmb/core/verifier.py`
- Create `tests/test_journal.py`
- Create `tests/test_verifier.py`

### Journal behavior

Official source:

```text
https://www.biodiversity-science.net/CN/column/column49.shtml
```

`default_contract()` returns:

```text
journal_name: 生物多样性
main_language: zh-CN
bilingual_elements: title, abstract, keywords
source_url: official URL
status: cached
```

`refresh_contract(project, fetcher=...)`:

- uses injectable fetcher for tests;
- stores retrieval timestamp and SHA-256 content hash;
- marks `fresh` on success;
- preserves existing cached rules and marks `stale` on failure;
- never parses changing journal prose into unsupported hard requirements.

### Package verifier

`PackageVerifier(project).verify(author=None, package=None)` returns:

```text
maximum_level
findings
blocking
```

Finding fields:

```text
code
kind: deterministic|heuristic
blocking
message
artifact
```

Deterministic blockers:

- `Dr. Who` or other placeholder author;
- missing required authorship/declarations;
- missing bilingual title/abstract/keywords;
- citation/reference set mismatch;
- failed sensitive-data check;
- missing central claim trace;
- failed analysis cited as support.

Heuristic findings never block.

### Required tests

- default contract;
- successful refresh and content hash;
- failed refresh marks stale without losing cache;
- placeholder author caps maximum at Level 3;
- confirmed metadata can reach candidate Level 4 if all deterministic checks
  pass;
- heuristic weakness does not block;
- deterministic failure blocks;
- provenance findings integrate without duplicating Gate policy.

### Verification

```powershell
python -m pytest tests/test_journal.py tests/test_verifier.py -q
python -m pytest -q
git diff --check
```

**Commit:**

```text
feat: verify journal submission packages
```

## 11. H7: Final CLI, Adapter Parity, and End-to-End Workflow

**Dependency:** H6.

**Owned files:**

- Modify `wmb/cli.py`
- Modify `wmb/__main__.py` only if required
- Create `tests/conftest.py`
- Create `tests/test_adapter_conformance.py`
- Create `tests/test_end_to_end.py`
- Create `tests/fixtures/basic_project/project.yaml`

### Add CLI commands

```text
wmb transition PROJECT --to STATUS --decision DECISION --reason REASON
wmb resume PROJECT
wmb verify PROJECT
wmb journal refresh PROJECT
```

`wmb status` must report:

```text
run_id
status
current_gate
delivery_level
target_journal
author_status
pending_author_confirmations
task counts by status
latest event ID
blocking issues
```

### Adapter parity

Given the same task and valid result:

- Codex and Hermes ingestion return the same recommended transition;
- neither adapter changes canonical Gate state;
- core Gate Engine decides the next action;
- repeated ingestion is idempotent.

### End-to-end acceptance test

Test this full path without external network or live Hermes task creation:

```text
initialize project
→ create analysis task
→ prepare Hermes dispatch
→ ingest usable_with_caveat result
→ record analysis provenance
→ record central claim trace
→ create isolated reviewer task
→ ingest review
→ auto-refine one low-risk issue
→ recover after simulated interruption
→ verify package
→ stop at Level 3 because Dr. Who remains placeholder
```

Then confirm real confirmed author metadata removes only the author blocker;
other deterministic failures remain blocking.

### Verification

```powershell
python -m pytest tests/test_adapter_conformance.py tests/test_end_to_end.py tests/test_cli.py -q
python -m pytest -q

$smoke = Join-Path $env:TEMP 'wmb-h7-smoke'
python -m wmb init $smoke
python -m wmb status $smoke
python -m wmb resume $smoke
python -m wmb verify $smoke
```

Expected: commands succeed; verification reports maximum Level 3 or lower
because author confirmation is pending.

**Commit:**

```text
feat: complete cross-platform WMB workflow
```

## 12. H8: Skill and Operator Documentation

**Dependency:** H7.

**Owned files:**

- Modify `SKILL.md`
- Create `references/multi-agent-workflow.md`
- Modify `references/run-lessons.md`
- Modify `references/journal-target-contract.md`
- Modify `references/literature-search-fallback.md`
- Create `tests/test_skill_references.py`

Do not rewrite the entire 31-step workflow.

### Required documentation changes

Add an early `Executable Multi-Agent Workflow` section to `SKILL.md` that:

- routes executable runs to `references/multi-agent-workflow.md`;
- states `.wmb/` is canonical;
- lists author confirmation moments;
- states default `Dr. Who` and 《生物多样性》 behavior;
- explains Level 3 versus candidate Level 4;
- gives Codex and Hermes start/resume/status commands.

`references/multi-agent-workflow.md` must document:

```text
wmb init
wmb status
wmb task create
wmb dispatch
wmb result ingest
wmb change evaluate
wmb resume
wmb verify
wmb journal refresh
```

It must explain:

- Hermes Durable Kanban for durable tasks;
- `delegate_task` only for small non-durable exploration;
- Codex task packet behavior;
- Worker/Reviewer isolation;
- failure and recovery behavior;
- no direct editing of `.wmb/run.yaml`.

Change `references/run-lessons.md` from automatic injection to:

```text
capture candidate lesson
→ author approval
→ versioned publication
→ explicit project enablement
```

Change `references/journal-target-contract.md` so missing journal defaults to
《生物多样性》 and cached official instructions become `stale` when refresh
fails.

Change `references/literature-search-fallback.md`:

- never include an API-key-looking literal;
- never instruct readers to access a Hermes `.env` path;
- read credentials only from the process environment;
- preserve proxy settings instead of removing them globally.

Remove the Hermes `.env` instruction from `SKILL.md` at the same time.

### Required tests

- every local `references/*.md` link in `SKILL.md` exists;
- `SKILL.md` mentions `.wmb/`, Codex, Hermes, `Dr. Who`, and 《生物多样性》;
- run-lessons no longer contains automatic Hermes injection instructions;
- literature fallback contains no key-shaped placeholder or `.env` path.

### Verification

```powershell
python -m pytest tests/test_skill_references.py -q
python -m pytest -q
git diff --check
```

**Commit:**

```text
docs: document executable multi-agent workflow
```

## 13. H9: Final Acceptance and GitHub Checkpoint

**Dependency:** H8.

**Owned files:**

- Create `docs/superpowers/reports/2026-06-14-v1-acceptance.md`
- Modify only files required to fix failed acceptance tests.

### Required acceptance commands

```powershell
git switch feat/multi-agent-workflow
git status --short --branch
python -m pytest -q
python -m compileall -q wmb
python -m pip wheel . --no-deps --wheel-dir "$env:TEMP\wmb-wheel"
git diff --check
```

CLI smoke:

```powershell
$project = Join-Path $env:TEMP 'wmb-final-smoke'
python -m wmb init $project
python -m wmb status $project
$task = python -m wmb task create $project --capability manuscript_writer --objective 'Draft Methods' --output '.wmb/artifacts/methods.md' | ConvertFrom-Json
python -m wmb verify $project
python -m wmb resume $project
```

Module existence check:

```powershell
python -c "import wmb.core.gate_engine,wmb.core.loop_controller,wmb.core.logging,wmb.core.provenance,wmb.core.journal,wmb.core.verifier,wmb.core.recovery,wmb.adapters.base,wmb.adapters.codex,wmb.adapters.hermes,wmb.__main__"
```

Hermes command inspection:

```powershell
python -m wmb dispatch $project $task.task_id --platform hermes
```

The printed command must use:

```text
hermes kanban create
```

and must not execute without `--execute`.

### Acceptance report

The report must contain:

- branch and final commit;
- test count;
- CLI smoke results;
- module checklist;
- final acceptance checklist below;
- deferred findings;
- explicit statement that `main` was not merged automatically.

### Final acceptance checklist

- `.wmb/` remains the sole canonical state source.
- Only StateStore performs legal canonical transitions.
- Worker and Reviewer contexts are isolated.
- Major scientific changes request author confirmation.
- Low-risk revisions loop automatically and finitely.
- Failures, exclusions, retries, and skips are logged.
- Analysis and central claims are traceable.
- Deterministic package failures block; heuristics only warn.
- `Dr. Who` prevents Level 4.
- 《生物多样性》 is default and refresh failures become stale cache.
- Codex and Hermes adapters preserve identical core policy.
- Interrupted work resumes without duplicating unchanged completed work.
- User-facing skill instructions cover start, status, resume, and verify.
- All tests pass.

### Final GitHub checkpoint

```powershell
git add docs/superpowers/reports/2026-06-14-v1-acceptance.md
git commit -m "test: verify WMB V1 workflow"
git push origin feat/multi-agent-workflow
git ls-remote --heads origin feat/multi-agent-workflow
```

Do not merge to `main`. Leave the pushed feature branch ready for user review.

## 14. Hermes Controller Prompt

Give the following prompt to Hermes from the repository directory:

```text
Execute the completion plan at:
C:\Users\Administrator\.codex\skills\wildlife-manuscript-builder\docs\superpowers\plans\2026-06-14-hermes-v1-completion-plan.md

Use Hermes Durable Kanban board `wmb-v1-completion`.
Create exactly ten serial cards H0 through H9 using the card sections in the
plan. Set every child to depend on the preceding card. Use assignee `default`,
workspace
`dir:C:\Users\Administrator\.codex\skills\wildlife-manuscript-builder`,
branch `feat/multi-agent-workflow`, max retries 2, and dispatch at most one
writer at a time.

Follow the execution rules and card completion protocol exactly. Do not merge
to main. Do not redesign the already-completed Task 1-4 foundation. Prioritize
the H3 executable Hermes vertical slice. If a card encounters a non-blocking
quality suggestion after its single repair round, record it as `DEFERRED:` and
continue. Block only for a failed listed acceptance behavior, data loss,
restricted-data leak, author-confirmation bypass, false Level 4 status, or an
unresolvable external dependency.

After creating the graph, run one dry dispatch, verify only H0 is ready, then
start execution with dispatch max 1. Continue until H9 is complete or a card
meets the explicit blocking criteria.
```

## 15. Suggested Manual Board Bootstrap

If Hermes does not create the board automatically:

```powershell
Set-Location 'C:\Users\Administrator\.codex\skills\wildlife-manuscript-builder'

hermes kanban boards create wmb-v1-completion `
  --name 'WMB V1 Completion' `
  --description 'Complete the executable Codex/Hermes manuscript workflow' `
  --default-workdir 'C:\Users\Administrator\.codex\skills\wildlife-manuscript-builder' `
  --switch

hermes kanban create 'H0 Baseline and remote checkpoint' `
  --body 'Execute H0 from docs/superpowers/plans/2026-06-14-hermes-v1-completion-plan.md exactly.' `
  --assignee default `
  --workspace 'dir:C:\Users\Administrator\.codex\skills\wildlife-manuscript-builder' `
  --branch feat/multi-agent-workflow `
  --idempotency-key wmb-v1-h0 `
  --max-runtime 1h `
  --max-retries 2 `
  --goal `
  --goal-max-turns 6
```

Create H1-H9 in the same manner with idempotency keys `wmb-v1-h1` through
`wmb-v1-h9`, and link each preceding task as the parent of the next task.

Before starting:

```powershell
hermes kanban list
hermes kanban dispatch --dry-run --max 1
```

Start:

```powershell
hermes kanban dispatch --max 1 --failure-limit 2
```

Monitor:

```powershell
hermes kanban list
hermes kanban diagnostics
hermes kanban stats
```
