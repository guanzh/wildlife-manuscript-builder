# Wildlife Manuscript Builder Multi-Agent Workflow Design

**Date:** 2026-06-12  
**Status:** Approved design  
**Target release:** V1  
**Primary platforms:** Codex and Hermes

## 1. Purpose

Wildlife Manuscript Builder (WMB) already provides a strong ecology-specific
manuscript workflow, including evidence boundaries, result cards, claim
ledgers, statistical delivery gates, reviewer simulation, and submission
readiness checks. However, the workflow is primarily expressed as prose in
`SKILL.md` and reference documents.

V1 converts that prose workflow into a resumable, finite, multi-agent system
that can:

- dynamically assemble a team for the manuscript at hand;
- run approved R or Python analyses through a statistician agent;
- automatically revise low-risk issues in bounded loops;
- pause for the author only at defined scientific and submission decisions;
- resume the same project from Codex or Hermes;
- produce a candidate submission package without overstating readiness.

The orchestration core is platform-neutral. Codex and Hermes are execution
adapters, not independent implementations of the scientific workflow.

## 2. Design Decisions

### 2.1 Selected approach

Embed a lightweight executable orchestrator inside the existing WMB skill.
The orchestrator uses project-local YAML and JSON records under `.wmb/` as its
cross-platform source of truth.

This approach preserves the existing domain-specific skill while adding real
state management, contracts, recovery, and verification. It avoids turning
`SKILL.md` into a larger prompt-only protocol and avoids creating a separate
generic orchestration product in V1.

### 2.2 Human involvement boundary

The workflow requests author confirmation only for:

1. the research direction and primary question;
2. a major change to the core analysis;
3. the final candidate submission package;
4. real author identity, order, affiliations, contributions, permits, and
   submission declarations.

Low-risk revisions proceed automatically within bounded loops.

### 2.3 Lifecycle boundary

V1 ends at a candidate Level 4 submission package. It does not include journal
submission, editor communication, reviewer-response cycles, or post-submission
revision.

### 2.4 Dynamic team

WMB selects agents by required capability rather than using a fixed roster.
For example, a camera-trap occupancy project may require an occupancy
statistician, camera-trap ecologist, sensitive-location reviewer, writer, and
statistical reviewer. A different project receives a different team.

## 3. Scope

### 3.1 V1 scope

V1 includes:

- a platform-neutral Python orchestration core;
- a single state writer and legal state-transition engine;
- a persistent project passport and append-only event ledger;
- machine-validatable agent task and result contracts;
- dynamic capability routing;
- generator and reviewer context isolation;
- bounded revision loops with improvement tracking;
- analysis-run provenance and claim/result/reference traceability;
- a structured rejection and exception ledger;
- deterministic submission-package verification;
- a Codex adapter;
- a Hermes adapter;
- adapter conformance and recovery tests;
- default author and journal behavior;
- repair of the two currently missing reference documents.

### 3.2 V2 candidates

V2 may add:

- block-addressed manuscript revision patches;
- default cross-model independent audits;
- ecology-specific reviewer calibration and gold fixtures;
- expanded literature corpus adapters;
- a versioned, author-approved cross-project lesson system.

### 3.3 Non-goals

V1 will not:

- submit manuscripts to journals;
- guarantee acceptance or scientific correctness;
- claim byte-for-byte reproducibility of LLM output;
- let platform adapters implement their own Gate logic;
- silently exclude sources, rows, claims, or failed tasks;
- automatically publish or inject lessons into later projects;
- treat a generic numeric paper-quality score as ground truth.

## 4. Architecture

```text
wildlife-manuscript-builder/
├── SKILL.md
├── wmb/
│   ├── core/
│   │   ├── state_machine.py
│   │   ├── state_store.py
│   │   ├── gate_engine.py
│   │   ├── task_router.py
│   │   ├── loop_controller.py
│   │   ├── provenance.py
│   │   └── verifier.py
│   ├── adapters/
│   │   ├── base.py
│   │   ├── codex.py
│   │   └── hermes.py
│   └── schemas/
├── references/
└── tests/
```

The core owns scientific workflow state, Gate decisions, loop policy,
contracts, provenance, and deterministic verification. Adapters only dispatch
tasks, collect structured results, and synchronize platform execution status.

## 5. Project State

Each manuscript project receives a `.wmb/` directory:

```text
.wmb/
├── run.yaml
├── journal_contract.yaml
├── author_confirmation_queue.yaml
├── tasks/
├── artifacts/
├── reviews/
├── decisions/
└── logs/
```

### 5.1 Source of truth

`.wmb/` is the sole cross-platform source of truth. Codex task state, Hermes
Kanban state, chat history, and agent-local notes are execution aids only.

### 5.2 Single state writer

Only the orchestrator's state-store component may change canonical workflow
state. Worker and reviewer agents submit structured results and recommended
transitions, but cannot directly advance, downgrade, or block the run.

### 5.3 Append-only events

Every state change appends an event containing:

- event identifier and timestamp;
- actor and event type;
- previous and resulting state;
- reason;
- relevant task and artifact identifiers;
- artifact hashes when applicable.

The current state in `run.yaml` is a projection of valid events. The event
ledger enables audit, resume, and mismatch repair.

## 6. State and Gate Model

The existing WMB decisions remain canonical:

- `PROCEED`
- `REFINE`
- `DOWNGRADE`
- `BLOCK`

The state machine makes legal transitions executable. An agent recommendation
cannot cause an illegal transition.

Major workflow states are:

1. intake and data-contract review;
2. research-direction confirmation;
3. evidence and analysis;
4. result-card and claim-ledger construction;
5. manuscript drafting;
6. independent review and bounded revision;
7. package verification;
8. final author confirmation;
9. candidate Level 4 completion or an honest lower-level outcome.

`BLOCK` must include explicit unblock conditions. `DOWNGRADE` must identify the
smallest defensible deliverable, such as a monitoring baseline, data note,
local report, or methods note.

## 7. Agent Model

### 7.1 Control components

- **Orchestrator:** routes tasks and evaluates structured results.
- **State Store:** validates and writes canonical state and events.
- **Gate Engine:** applies deterministic Gate and author-confirmation policy.
- **Package Verifier:** runs deterministic and heuristic package checks.

Control components do not vote on scientific conclusions.

### 7.2 Worker agents

Worker agents perform bounded tasks such as literature research, statistical
analysis, ecological interpretation, figure preparation, and manuscript
writing. A statistician agent may write and run R or Python analysis.

### 7.3 Reviewer agents

Reviewer agents inspect candidate artifacts and return findings and verdict
recommendations. A reviewer must not evaluate an artifact in the same context
that generated it.

For high-risk Gates, the reviewer freezes its review dimensions and failure
conditions before receiving the candidate artifact.

### 7.4 Dynamic capability routing

The task router selects capabilities from the data type, method, target
journal, risk profile, and current Gate. It does not require a fixed number of
agents.

All scientifically plausible research-direction candidates remain visible to
the author. The router must not silently hide alternatives through an internal
top-K selection.

## 8. Task Contracts

Every agent invocation receives a machine-validatable task contract containing:

```yaml
task_id: analysis-001
capability: occupancy_statistician
objective: Fit candidate occupancy models and create result cards
allowed_inputs:
  - data/camera_trap.csv
  - .wmb/artifacts/study_design.yaml
required_outputs:
  - .wmb/artifacts/analysis/occupancy_result_card.yaml
  - .wmb/artifacts/analysis/model_diagnostics.md
acceptance_criteria:
  - report estimates and uncertainty
  - record exclusions and reasons
  - distinguish association from causation
prohibited_actions:
  - change the response variable without author confirmation
  - exclude key samples without author confirmation
  - change the core inferential target without author confirmation
max_attempts: 3
```

Agent results contain:

- task identifier and completion status;
- created or modified artifact identifiers;
- findings and unresolved issues;
- recommended transition;
- confidence and limitations;
- failures, exclusions, or skipped work.

The core validates results before accepting them.

## 9. Data Access and Isolation

Task contracts explicitly list allowed inputs. V1 distinguishes:

- raw project data;
- verified analysis artifacts;
- manuscript and writing artifacts;
- review-only artifacts and criteria;
- sensitive or restricted materials.

Reviewer contexts do not inherit worker conversations. Sensitive materials are
provided only to capabilities that require them. A task attempting to access
an unlisted artifact fails contract validation.

## 10. Analysis and Claim Provenance

Every analysis run records:

- planned analysis and decision context;
- executed command or script;
- input file hashes;
- outputs and result-card pointers;
- warnings, errors, and diagnostics;
- exclusions and reasons;
- negative or null results;
- known limitations;
- environment and dependency lock information.

The claim ledger is extended into an explicit trace:

```text
planned claim
→ analysis run or evidence source
→ result card
→ emitted manuscript claim
→ figure or table caption
```

A central manuscript claim without a valid trace cannot pass the relevant
Gate. A failed analysis cannot be cited as supporting evidence.

## 11. Revision Loops

### 11.1 Automatically permitted revisions

The workflow may automatically:

- narrow unsupported or overly strong claims;
- repair citation and reference mismatches;
- synchronize prose, figures, tables, and result cards;
- improve language and structure;
- add missing method descriptions supported by existing materials;
- repair formatting and deterministic journal-package issues.

### 11.2 Author-confirmation triggers

The workflow pauses before:

- changing the research question or core hypothesis;
- changing the response variable, core model, or inferential target;
- excluding key samples or changing key inclusion criteria;
- changing direction because results cannot support the confirmed question;
- confirming the final candidate submission package;
- confirming real author and submission metadata.

### 11.3 Finite-loop policy

Each loop records issue identifiers, changed artifacts, before-and-after
verdicts, newly introduced issues, and the stop reason.

The loop stops when:

- the Gate passes;
- no blocking issue remains and a round produces no material improvement;
- the same blocking issue fails to improve for two consecutive rounds;
- three revision rounds are reached;
- an author-confirmation trigger occurs.

Material improvement means at least one blocking issue is resolved, an issue
severity is reduced, or required evidence-trace coverage increases. Language
changes without one of those effects do not count as material improvement.

At the limit, the core selects `BLOCK`, `DOWNGRADE`, or an author decision. It
never loops indefinitely.

## 12. Author and Journal Defaults

When no author is supplied:

```yaml
display_name: Dr. Who
status: placeholder
```

`Dr. Who` is always visibly marked as a placeholder. Missing real author
identity, order, affiliations, contributions, permits, or declarations limits
the run to Level 3. Missing information is collected in
`author_confirmation_queue.yaml` while other work continues.

When no journal is supplied, the target journal is 《生物多样性》. The default
manuscript has Chinese main text plus Chinese and English titles, abstracts,
and keywords.

The journal contract is refreshed from the official journal instructions at
`https://www.biodiversity-science.net/CN/column/column49.shtml` at runtime when
possible. The contract records source URL, retrieval date, and content hash.
If refresh fails, the cached contract is used and marked `stale`.

## 13. Platform Adapters

### 13.1 Codex adapter

The Codex adapter:

- dispatches dynamic worker and reviewer agents using Codex multi-agent tools;
- permits parallel independent tasks;
- validates and writes returned results through the core;
- resumes from `.wmb/` rather than relying on thread memory.

### 13.2 Hermes adapter

The Hermes adapter:

- maps durable cross-session tasks to Hermes Durable Kanban;
- maps dependencies and capability profiles;
- uses isolated workspaces where needed;
- uses `delegate_task` only for small, non-durable parallel exploration;
- synchronizes completed results through the core.

Hermes task storage remains an execution queue. It never replaces `.wmb/`.

### 13.3 Adapter parity

Given the same valid project state and structured agent result, Codex and
Hermes adapters must produce the same canonical Gate decision. Adapter-specific
status must not alter scientific policy.

## 14. Recovery and Consistency

On resume, the core:

1. validates `.wmb/` records against schemas;
2. verifies the latest completed event and referenced artifact hashes;
3. marks running tasks without valid outputs as retryable;
4. avoids rerunning completed tasks whose inputs and outputs are unchanged;
5. detects adapter-state mismatches and repairs platform mappings from `.wmb/`.

Corrupt canonical state, invalid transitions, or untraceable central evidence
block the run. Recovery never guesses a scientific decision.

## 15. Error and Logging Policy

The following conditions block progression:

- corrupt state or an illegal transition;
- untraceable core data, analysis results, citations, or claims;
- failed worker/reviewer isolation;
- a manuscript claim relying on a failed analysis;
- sensitive-location or privacy leakage risk;
- fabricated authors, references, or declarations;
- an unconfirmed placeholder presented as submission-ready.

Temporary agent failures, non-core tool failures, formatting failures, and
low-risk synchronization issues may be retried within their contracts.

Every failure, skip, exclusion, retry, dropped claim, and rejected source is
recorded with a reason. Silent skipping is forbidden.

## 16. Submission-Package Verification

Package checks are separated into:

- **deterministic checks**, which may block progression;
- **heuristic checks**, which may warn but cannot independently block.

Deterministic V1 checks include:

- required sections and bilingual elements;
- citation/reference set consistency;
- required figures, tables, and metadata;
- author-placeholder and confirmation status;
- sensitive-location and privacy checks;
- traceability of central claims;
- applicable 《生物多样性》 contract requirements.

Heuristic findings include possible discussion weakness, language strength, and
reviewer-risk concerns. They remain visible but advisory.

## 17. Reproducibility Record

Each run records:

- WMB Git commit and skill hash;
- adapter and runtime versions;
- model identifiers where available;
- task contracts and returned results;
- input and artifact hashes;
- analysis environment lock;
- journal-contract source date and hash.

This record supports audit and difference investigation. It does not claim that
LLM output can be reproduced byte for byte.

## 18. Testing Strategy

V1 uses focused ecology fixtures and automated tests for:

- legal and illegal state transitions;
- three-round loop limits and early stopping;
- author confirmation on major analysis changes;
- task-contract and result-contract validation;
- worker/reviewer isolation;
- analysis-to-claim traceability;
- `Dr. Who` placeholder blocking Level 4;
- default 《生物多样性》 journal contract;
- identical core Gate decisions through Codex and Hermes adapters;
- interruption recovery without duplicate completed work;
- sensitive-data and fabricated-reference blocking;
- deterministic versus heuristic verifier policy;
- no-silent-skip logging.

Tests are added incrementally with the implementation. V1 does not reproduce
the size of the reference repository's test suite.

## 19. Migration of Existing Skill Content

The existing 31-step workflow, domain routing, result cards, claim ledger,
decision loop, Figure-Claim Trace, reviewer simulation, and quality gates
remain domain guidance. The executable core references and enforces them where
deterministic enforcement is possible.

V1 also repairs the currently referenced but missing files:

- `references/rewriting-existing-manuscript.md`
- `references/literature-search-fallback.md`

The current `run-lessons.md` behavior is changed from automatic cross-project
injection to:

```text
capture candidate lesson
→ author approval
→ versioned publication
→ explicit project enablement
```

## 20. Reference Repository Influence

The design borrows architectural ideas from
`Imbad0202/academic-research-skills`, especially persistent passports,
single-writer state control, machine-validatable handoffs, finite loops,
generator/reviewer separation, provenance, and deterministic package checks.

That repository uses the CC BY-NC 4.0 license. WMB will clean-room implement
the approved concepts and will not directly copy its code, schemas, or prose.

WMB intentionally differs by:

- providing an executable platform-neutral core;
- supporting both Codex and Hermes;
- allowing approved R and Python analysis execution;
- using only defined author decision points;
- using a dynamic rather than fixed agent team;
- retaining wildlife and ecology-specific evidence safeguards.

## 21. Acceptance Criteria

V1 is complete when:

1. a new manuscript project can initialize valid `.wmb/` state;
2. the same project can pause in one supported platform and resume in the
   other without losing or duplicating completed work;
3. only the state store can make legal canonical transitions;
4. dynamically routed workers and isolated reviewers exchange validated
   contracts and results;
5. low-risk revisions loop automatically and stop under the finite-loop policy;
6. major scientific changes create an author-confirmation request;
7. analysis runs, central claims, result cards, and figure/table captions are
   traceable;
8. missing real authorship or declarations prevents Level 4;
9. deterministic package failures block while heuristic findings only warn;
10. the Codex and Hermes adapter conformance fixtures pass;
11. the full automated test suite passes;
12. user-facing skill instructions explain how to start, resume, inspect, and
    complete a WMB run on both platforms.
