"""Command-line surface for Wildlife Manuscript Builder — using real core."""

from __future__ import annotations

import argparse
import json
import sys
import uuid as _uuid
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import yaml

from wmb import __version__
from wmb.contracts import validate_contract, ContractError
from wmb.core.project import initialize_project
from wmb.core.state_store import StateStore, StateConsistencyError, IllegalTransition as STIllegal
from wmb.core.state_machine import validate_transition, IllegalTransition
from wmb.core.models import ProjectPaths


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="wmb",
        description="Wildlife Manuscript Builder",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="Initialize a project")
    p_init.add_argument("project", help="Project directory path")
    p_init.add_argument("--author", default=None, help="Author name (default: Dr. Who)")

    p_status = sub.add_parser("status", help="Show project status")
    p_status.add_argument("project")

    p_task = sub.add_parser("task", help="Task management")
    p_task_s = p_task.add_subparsers(dest="task_command", required=True)
    p_tc = p_task_s.add_parser("create", help="Create a task")
    p_tc.add_argument("project")
    p_tc.add_argument("--capability", required=True)
    p_tc.add_argument("--objective", required=True)

    p_dispatch = sub.add_parser("dispatch", help="Dispatch a task")
    p_dispatch.add_argument("project")
    p_dispatch.add_argument("task_id")
    p_dispatch.add_argument("--platform", required=True, choices=["codex", "hermes"])

    p_result = sub.add_parser("result", help="Ingest a task result")
    p_result_s = p_result.add_subparsers(dest="result_command", required=True)
    p_ri = p_result_s.add_parser("ingest", help="Ingest result file")
    p_ri.add_argument("project")
    p_ri.add_argument("result_file")
    p_ri.add_argument("--platform", required=True, choices=["codex", "hermes"])

    p_change = sub.add_parser("change", help="Change evaluation")
    p_change_s = p_change.add_subparsers(dest="change_command", required=True)
    p_ce = p_change_s.add_parser("evaluate", help="Evaluate a change")
    p_ce.add_argument("project")
    p_ce.add_argument("change_file")

    p_transition = sub.add_parser("transition", help="Transition run status")
    p_transition.add_argument("project")
    p_transition.add_argument("--to", required=True, dest="transition_to")
    p_transition.add_argument("--decision", required=True)
    p_transition.add_argument("--reason", required=True)

    p_resume = sub.add_parser("resume", help="Resume interrupted run")
    p_resume.add_argument("project")

    p_verify = sub.add_parser("verify", help="Verify submission package")
    p_verify.add_argument("project")

    p_jr = sub.add_parser("journal", help="Journal management")
    p_jr_s = p_jr.add_subparsers(dest="journal_command", required=True)
    p_jrr = p_jr_s.add_parser("refresh", help="Refresh journal contract")
    p_jrr.add_argument("project")

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return int(exc.code)

    cmd = args.command
    try:
        if cmd == "init":
            return _cmd_init(args)
        elif cmd == "status":
            return _cmd_status(args)
        elif cmd == "task":
            if args.task_command == "create":
                return _cmd_task_create(args)
            return _unknown("task", args.task_command)
        elif cmd == "dispatch":
            return _cmd_dispatch(args)
        elif cmd == "result":
            if args.result_command == "ingest":
                return _cmd_result_ingest(args)
            return _unknown("result", args.result_command)
        elif cmd == "change":
            if args.change_command == "evaluate":
                return _cmd_change_evaluate(args)
            return _unknown("change", args.change_command)
        elif cmd == "transition":
            return _cmd_transition(args)
        elif cmd == "resume":
            return _cmd_resume(args)
        elif cmd == "verify":
            return _cmd_verify(args)
        elif cmd == "journal":
            if args.journal_command == "refresh":
                return _cmd_journal_refresh(args)
            return _unknown("journal", args.journal_command)
        _unknown("", cmd)
        return 2
    except (IllegalTransition, STIllegal) as exc:
        _err(f"Illegal transition: {exc}")
        return 3
    except ContractError as exc:
        _err(f"Contract error: {exc}")
        return 2
    except Exception as exc:
        _err(f"Error: {exc}")
        return 2


# ---- command implementations ----

def _cmd_init(args: argparse.Namespace) -> int:
    """Use real initialize_project."""
    root = Path(args.project).resolve()
    author = {"name": args.author or "Dr. Who"} if args.author else {"name": "Dr. Who"}
    try:
        project = initialize_project(root, author=author)
    except Exception as exc:
        _err(f"Cannot initialize project: {exc}")
        return 2
    _out({
        "status": "ok",
        "project": str(project.root),
        "run_status": "intake",
    })
    return 0


def _cmd_status(args: argparse.Namespace) -> int:
    root = Path(args.project).resolve()
    run_file = root / ".wmb" / "run.yaml"
    if not run_file.exists():
        _out({"status": "not_found", "project": str(root)})
        return 0
    run = _load_yaml(run_file)
    _out({
        "status": "ok",
        "project": str(root),
        "run_status": run.get("status", "unknown"),
        "run_id": run.get("run_id", ""),
        "delivery_level": run.get("delivery_level", 0),
        "target_journal": run.get("target_journal", "生物多样性"),
        "author_status": run.get("author", {}).get("name", "Dr. Who"),
    })
    return 0


def _cmd_task_create(args: argparse.Namespace) -> int:
    """Create a real task contract file using schema validation."""
    root = Path(args.project).resolve()
    paths = ProjectPaths(root)
    if not paths.run_file.exists():
        _err("Project not initialized. Run 'wmb init' first.")
        return 2

    task_id = f"task-{_uuid.uuid4().hex[:12]}"
    capability = args.capability
    objective = args.objective

    task = {
        "task_id": task_id,
        "capability": capability,
        "objective": objective,
        "status": "pending",
        "role": "worker",
        "max_attempts": 3,
        "allowed_inputs": [],
        "required_outputs": [f".wmb/artifacts/{task_id}/output"],
        "acceptance_criteria": [],
        "context_id": f"ctx-{task_id}",
        "prohibited_actions": [],
    }
    try:
        validate_contract("task", task)
    except ContractError as exc:
        _err(f"Task contract invalid: {exc}")
        return 2

    paths.tasks_dir.mkdir(parents=True, exist_ok=True)
    task_file = paths.tasks_dir / f"{task_id}.yaml"
    task_file.write_text(yaml.safe_dump(task, default_flow_style=False, sort_keys=False), encoding="utf-8")

    _out({
        "status": "ok",
        "task_id": task_id,
        "capability": capability,
        "objective": objective,
        "task_file": str(task_file),
    })
    return 0


def _cmd_dispatch(args: argparse.Namespace) -> int:
    """Read persisted task, reject unknown task_id."""
    root = Path(args.project).resolve()
    paths = ProjectPaths(root)
    task_file = paths.tasks_dir / f"{args.task_id}.yaml"

    if not task_file.exists():
        _err(f"Unknown task_id: {args.task_id}. No task file found.")
        return 2

    task = _load_yaml(task_file)

    if args.platform == "hermes":
        from wmb.adapters.hermes import HermesAdapter
        adapter = HermesAdapter()
        cmd = adapter.build_create_command(task)
        _out({
            "status": "ok",
            "platform": "hermes",
            "command": " ".join(cmd),
            "note": "Use --execute to run. Dry-run by default.",
        })
        return 0
    elif args.platform == "codex":
        from wmb.adapters.codex import CodexAdapter
        adapter = CodexAdapter()
        packet = adapter.prepare_dispatch(task)
        _out({
            "status": "ok",
            "platform": "codex",
            "packet": {
                "adapter": packet.adapter,
                "objective": packet.objective,
                "capability": packet.capability,
                "isolated_context": packet.isolated_context,
            },
        })
        return 0
    return 2


def _cmd_result_ingest(args: argparse.Namespace) -> int:
    """Validate result against result.schema.json, check task existence."""
    root = Path(args.project).resolve()
    paths = ProjectPaths(root)

    if not paths.run_file.exists():
        _err("Project not initialized.")
        return 2

    result_path = Path(args.result_file)
    if not result_path.exists():
        _err(f"Result file not found: {result_path}")
        return 2

    try:
        result = json.loads(result_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        _err(f"Invalid JSON in result file: {exc}")
        return 2

    # Validate against result schema
    try:
        validate_contract("result", result)
    except ContractError as exc:
        _err(f"Result contract validation failed: {exc}")
        return 2

    # Check task exists
    task_id = result.get("task_id", "")
    task_file = paths.tasks_dir / f"{task_id}.yaml"
    if not task_file.exists():
        _err(f"Task {task_id} not found. Create the task first.")
        return 2

    # Persist result
    results_dir = paths.wmb_dir / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    result_file = results_dir / f"{task_id}.json"
    result_file.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    # Update task status
    if task_file.exists():
        task = _load_yaml(task_file)
        task["status"] = result.get("status", "completed")
        task["completed_at"] = __import__("datetime").datetime.now(
            __import__("datetime").timezone.utc
        ).isoformat().replace("+00:00", "Z")
        task_file.write_text(yaml.safe_dump(task, default_flow_style=False, sort_keys=False), encoding="utf-8")

    _out({
        "status": "ok",
        "task_updated": True,
        "errors": None,
    })
    return 0


def _cmd_change_evaluate(args: argparse.Namespace) -> int:
    path = Path(args.change_file)
    if not path.exists():
        _err(f"File not found: {path}")
        return 2
    change = json.loads(path.read_text(encoding="utf-8"))

    from wmb.core.gate_engine import GateEngine, GateDecision
    proj = _project_stub(Path(args.project))
    engine = GateEngine(proj)
    decision = engine.evaluate_change(change)

    output = {
        "status": decision.status.value if hasattr(decision.status, "value") else str(decision.status),
        "change_type": decision.change_type,
        "summary": decision.summary,
        "queue_item_id": decision.queue_item_id,
        "reason": decision.reason,
    }
    exit_code = 3 if decision.status.value.startswith("awaiting_author") else \
                2 if "blocked" in decision.status.value else 0
    _out(output)
    return exit_code


def _cmd_transition(args: argparse.Namespace) -> int:
    """Use real StateStore.transition with legal state machine check."""
    root = Path(args.project).resolve()
    paths = ProjectPaths(root)
    if not paths.run_file.exists():
        _err("Project not initialized.")
        return 2

    store = StateStore(paths)

    # Pre-validate: intake → candidate_level_4 is illegal
    run = store.load_run()
    from_status = run["status"]
    to_status = args.transition_to
    decision = args.decision

    try:
        validate_transition(from_status, to_status, decision)
    except IllegalTransition as exc:
        _err(f"Illegal transition: {exc}")
        return 3

    new_run = store.transition(
        actor="orchestrator",
        to_status=to_status,
        decision=decision,
        reason=args.reason,
    )

    # Verify events.jsonl was written (StateStore.transition does this)
    events_file = paths.events_log
    if events_file.exists():
        events_content = events_file.read_text(encoding="utf-8").strip()
        if events_content:
            _out({
                "status": "ok",
                "new_status": to_status,
                "from_status": from_status,
                "event_logged": True,
            })
            return 0

    _out({"status": "ok", "new_status": to_status})
    return 0


def _cmd_resume(args: argparse.Namespace) -> int:
    from wmb.core.recovery import RecoveryManager
    proj = _project_stub(Path(args.project))
    mgr = RecoveryManager(proj)
    report = mgr.recover()
    _out({
        "blocked": report.blocked,
        "retryable_tasks": report.retryable_tasks,
        "unchanged_completed": report.unchanged_completed_tasks,
        "issues": report.issues,
    })
    return 3 if report.blocked else 0


def _cmd_verify(args: argparse.Namespace) -> int:
    from wmb.core.verifier import PackageVerifier
    proj = _project_stub(Path(args.project))
    verifier = PackageVerifier(proj)
    report = verifier.verify()
    _out({
        "maximum_level": report.maximum_level,
        "blocking": report.blocking,
        "findings": [
            {"code": f.code, "kind": f.kind, "blocking": f.blocking, "message": f.message}
            for f in report.findings
        ],
    })
    return 3 if report.blocking else 0


def _cmd_journal_refresh(args: argparse.Namespace) -> int:
    from wmb.core.journal import JournalRefresh
    proj = _project_stub(Path(args.project))
    jr = JournalRefresh(proj)
    contract = jr.refresh_contract()
    _out({"journal_name": contract.journal_name, "status": contract.status})
    return 0


# ---- helpers ----

def _project_stub(project_dir: Path) -> Any:
    from types import SimpleNamespace
    proj = SimpleNamespace()
    proj.paths = SimpleNamespace()
    proj.paths.wmb_dir = project_dir / ".wmb"
    return proj


def _load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _out(data: dict[str, Any]) -> None:
    print(json.dumps(data, ensure_ascii=False))


def _err(msg: str) -> None:
    print(msg, file=sys.stderr)


def _unknown(parent: str, child: str) -> int:
    _err(f"Unknown {parent}command: {child}" if parent else f"Unknown command: {child}")
    return 2
