# WMB V1 Acceptance Report

**Date:** 2026-06-14
**Branch:** `feat/multi-agent-workflow`
**Final Commit:** `5bf4d72` — "docs: document executable multi-agent workflow"

## Test Results

```
451 passed in 19.62s
```

## CLI Smoke Results

| Command | Result |
|---------|--------|
| `wmb init PROJECT` | ✅ Status: intake |
| `wmb status PROJECT` | ✅ Shows 生物多样性, Dr. Who, intake |
| `wmb task create PROJECT --capability C --objective O` | ✅ task_id generated |
| `wmb dispatch PROJECT TASK_ID --platform hermes` | ✅ Uses `hermes kanban create` (dry-run safe) |
| `wmb change evaluate PROJECT CHANGE_FILE` | ✅ auto_refine and awaiting_author_confirmation |
| `wmb resume PROJECT` | ✅ Clean recovery report |
| `wmb verify PROJECT` | ✅ Correctly blocks on Dr. Who, missing bilingual elements |
| `wmb journal refresh PROJECT` | ✅ Stale/fresh contract caching |
| `python -m wmb --help` | ✅ All commands displayed |

## Module Checklist

| Module | Status |
|--------|--------|
| `wmb.core.gate_engine` | ✅ |
| `wmb.core.loop_controller` | ✅ |
| `wmb.core.logging` | ✅ |
| `wmb.core.provenance` | ✅ |
| `wmb.core.journal` | ✅ |
| `wmb.core.verifier` | ✅ |
| `wmb.core.recovery` | ✅ |
| `wmb.adapters.base` | ✅ |
| `wmb.adapters.codex` | ✅ |
| `wmb.adapters.hermes` | ✅ |
| `wmb.__main__` | ✅ |

## Acceptance Checklist

- [x] `.wmb/` remains the sole canonical state source
- [x] Only StateStore performs legal canonical transitions
- [x] Worker and Reviewer contexts are isolated
- [x] Major scientific changes request author confirmation
- [x] Low-risk revisions loop automatically and finitely
- [x] Failures, exclusions, retries, and skips are logged
- [x] Analysis and central claims are traceable
- [x] Deterministic package failures block; heuristics only warn
- [x] `Dr. Who` prevents Level 4
- [x] 生物多样性 is default and refresh failures become stale cache
- [x] Codex and Hermes adapters preserve identical core policy
- [x] Interrupted work resumes without duplicating unchanged completed work
- [x] User-facing skill instructions cover start, status, resume, and verify
- [x] All tests pass

## Deferred Findings

- `references/domain/method-checks/arrive.md` — could be expanded with WMB-specific check guidance (non-blocking)
- `tests/fixtures/basic_project/` — minimal fixture, could use more coverage (non-blocking)
- Hermes adapter `build_create_command` task body uses `unknown` capability when task capability not found — acceptable for V1 (non-blocking)
- Package verifier assumes `.wmb/artifacts/claims/` exists; fresh projects without claim traces always block — correct behavior (not a bug)

## Notes

- `main` was **not** merged automatically
- The `feat/multi-agent-workflow` branch is pushed and ready for user review
- H0–H9 Kanban cards are all completed on board `wmb-v1-completion`
