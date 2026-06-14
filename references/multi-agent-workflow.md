# Executable Multi-Agent Workflow

WMB integrates with both Codex and Hermes for durable task dispatch. This reference documents the `wmb` CLI workflow for project initialization through submission verification.

## Quick Start

```bash
# Initialize a new project
wmb init my-project

# Check status (defaults: Dr. Who, 生物多样性)
wmb status my-project

# Create a writing task
wmb task create my-project --capability manuscript_writer --objective "Draft Methods section"

# Create a review task (isolated context)
wmb task create my-project --capability reviewer --objective "Review Methods"

# Dispatch a task (Hermes Durable Kanban)
wmb dispatch my-project task_abc123 --platform hermes

# Verify submission package
wmb verify my-project
```

## Commands

| Command | Description | Example |
|---------|-------------|---------|
| `wmb init PROJECT` | Create a new `.wmb/` project | `wmb init ./paper` |
| `wmb status PROJECT` | Show run status, journal, author | `wmb status ./paper` |
| `wmb task create PROJECT --capability C --objective O` | Create a new task | See above |
| `wmb dispatch PROJECT TASK_ID --platform P` | Prepare dispatch (dry-run default) | `wmb dispatch . task-001 --platform hermes` |
| `wmb result ingest PROJECT FILE --platform P` | Ingest structured result | `wmb result ingest . result.json --platform hermes` |
| `wmb change evaluate PROJECT CHANGE_FILE` | Evaluate gate decision | See examples below |
| `wmb resume PROJECT` | Recover after interruption | `wmb resume .` |
| `wmb verify PROJECT` | Check submission readiness | `wmb verify .` |
| `wmb journal refresh PROJECT` | Refresh journal contract | `wmb journal refresh .` |
| `wmb transition PROJECT --to STATUS --decision D --reason R` | Transition run status | `wmb transition . --to drafting --decision proceed --reason "Gate 1 passed"` |

## Hermes Durable Kanban Integration

Use `hermes kanban` for durable task dispatch:

```bash
# Create and dispatch from WMB
wmb dispatch my-project task_001 --platform hermes
# Prints the safe command (does not execute):
#   hermes kanban create "Task ..." ...
```

Key behaviors:
- `delegate_task` is for small non-durable exploration only
- Hermes Durable Kanban is the primary durable execution mechanism
- Worker and Reviewer contexts are isolated
- Do not edit `.wmb/run.yaml` directly

## Failure and Recovery

If a run is interrupted:

```bash
wmb resume my-project
```

The recovery manager checks:
- Valid canonical run state and event audit
- Running tasks without valid outputs → retryable
- Completed tasks with unchanged outputs → skipped
- Changed completed outputs → blocks (user must confirm)
- Adapter state mismatches → reported for manual resolution

## File Summary

```
.wmb/
├── run.yaml              # Canonical workflow state
├── event_log.yaml        # State machine transitions
├── author_confirmation_queue.yaml  # Pending major-change approvals
├── adapter_state.yaml    # Platform adapter snapshot
├── journal_cache/
│   └── contract.yaml     # Cached journal requirements
├── logs/
│   └── rejections.jsonl  # Rejection ledger
├── artifacts/
│   ├── analysis/         # Analysis provenance records
│   └── claims/           # Claim trace records
└── tasks/                # Task contracts
```
