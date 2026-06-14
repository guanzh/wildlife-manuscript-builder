"""Command-line surface for Wildlife Manuscript Builder."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from wmb import __version__
from wmb.core.gate_engine import GateEngine
from wmb.core.loop_controller import LoopController
from wmb.adapters.hermes import HermesAdapter
from wmb.adapters.codex import CodexAdapter


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="wmb",
        description="Wildlife Manuscript Builder",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="Initialize a project")
    p_init.add_argument("project", help="Project directory path")

    p_status = sub.add_parser("status", help="Show project status")
    p_status.add_argument("project", help="Project directory path")

    p_task = sub.add_parser("task", help="Task management")
    p_task_sub = p_task.add_subparsers(dest="task_command", required=True)
    p_task_create = p_task_sub.add_parser("create", help="Create a task")
    p_task_create.add_argument("project", help="Project directory path")
    p_task_create.add_argument("--capability", required=True)
    p_task_create.add_argument("--objective", required=True)
    p_task_create.add_argument("--input", dest="input_path")
    p_task_create.add_argument("--output", dest="output_path")

    p_dispatch = sub.add_parser("dispatch", help="Dispatch a task")
    p_dispatch.add_argument("project", help="Project directory path")
    p_dispatch.add_argument("task_id", help="Task ID")
    p_dispatch.add_argument("--platform", required=True, choices=["codex", "hermes"])

    p_ingest = sub.add_parser("result", help="Ingest a task result")
    p_ingest_sub = p_ingest.add_subparsers(dest="result_command", required=True)
    p_ingest_run = p_ingest_sub.add_parser("ingest", help="Ingest result file")
    p_ingest_run.add_argument("project", help="Project directory path")
    p_ingest_run.add_argument("result_file", help="Path to result JSON file")
    p_ingest_run.add_argument("--platform", required=True, choices=["codex", "hermes"])

    p_change = sub.add_parser("change", help="Change evaluation")
    p_change_sub = p_change.add_subparsers(dest="change_command", required=True)
    p_change_eval = p_change_sub.add_parser("evaluate", help="Evaluate a change")
    p_change_eval.add_argument("project", help="Project directory path")
    p_change_eval.add_argument("change_file", help="Path to change JSON file")

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the WMB command-line interface."""
    parser = _parser()

    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return int(exc.code)

    command = args.command
    try:
        if command == "init":
            return _cmd_init(args)
        elif command == "status":
            return _cmd_status(args)
        elif command == "task":
            if args.task_command == "create":
                return _cmd_task_create(args)
            print(f"Unknown task command: {args.task_command}", file=sys.stderr)
            return 2
        elif command == "dispatch":
            return _cmd_dispatch(args)
        elif command == "result":
            return _cmd_result_ingest(args)
        elif command == "change":
            if args.change_command == "evaluate":
                return _cmd_change_evaluate(args)
            print(f"Unknown change command: {args.change_command}", file=sys.stderr)
            return 2
        else:
            print(f"Unknown command: {command}", file=sys.stderr)
            return 2
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 3


def _cmd_init(args: argparse.Namespace) -> int:
    path = Path(args.project)
    wmb_dir = path / ".wmb"
    wmb_dir.mkdir(parents=True, exist_ok=True)
    (wmb_dir / "run.yaml").write_text("status: intake\n", encoding="utf-8")
    (wmb_dir / "event_log.yaml").write_text("events: []\n", encoding="utf-8")
    output = {
        "status": "ok",
        "project": str(path.resolve()),
        "run_status": "intake",
    }
    print(json.dumps(output, ensure_ascii=False))
    return 0


def _cmd_status(args: argparse.Namespace) -> int:
    path = Path(args.project)
    wmb_dir = path / ".wmb"
    run_yaml = wmb_dir / "run.yaml"
    if not run_yaml.exists():
        print(json.dumps({"status": "not_found", "project": str(path)}))
        return 0

    import yaml
    with open(str(run_yaml), encoding="utf-8") as fh:
        run_data = yaml.safe_load(fh) or {}

    output = {
        "status": "ok",
        "project": str(path.resolve()),
        "run_status": run_data.get("status", "unknown"),
        "target_journal": run_data.get("target_journal", "生物多样性"),
        "author_status": run_data.get("author_status", "Dr. Who"),
    }
    print(json.dumps(output, ensure_ascii=False))
    return 0


def _cmd_task_create(args: argparse.Namespace) -> int:
    import uuid
    task_id = f"task_{uuid.uuid4().hex[:8]}"
    task = {
        "task_id": task_id,
        "capability": args.capability,
        "objective": args.objective,
        "input_path": args.input_path,
        "output_path": args.output_path,
    }
    print(json.dumps({"status": "ok", "task_id": task_id, "task": task}, ensure_ascii=False))
    return 0


def _cmd_dispatch(args: argparse.Namespace) -> int:
    task = {"task_id": args.task_id, "objective": f"Task {args.task_id}", "capability": "unknown"}
    if args.platform == "hermes":
        adapter = HermesAdapter()
        cmd = adapter.build_create_command(task)
        result = {
            "status": "ok",
            "platform": "hermes",
            "command": " ".join(cmd),
            "note": "Use --execute to run. Dry-run by default.",
        }
        print(json.dumps(result, ensure_ascii=False))
        return 0
    elif args.platform == "codex":
        adapter = CodexAdapter()
        packet = adapter.prepare_dispatch(task)
        print(json.dumps({
            "status": "ok",
            "platform": "codex",
            "packet": {
                "adapter": packet.adapter,
                "objective": packet.objective,
                "capability": packet.capability,
                "isolated_context": packet.isolated_context,
            },
        }, ensure_ascii=False))
        return 0
    return 2


def _cmd_result_ingest(args: argparse.Namespace) -> int:
    path = Path(args.result_file)
    if not path.exists():
        print(json.dumps({"status": "error", "error": f"File not found: {path}"}, ensure_ascii=False))
        return 2

    import yaml
    try:
        with open(str(path), encoding="utf-8") as fh:
            result = json.load(fh)
    except (json.JSONDecodeError, Exception) as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False))
        return 2

    if args.platform == "hermes":
        adapter = HermesAdapter()
    else:
        adapter = CodexAdapter()

    ingest_result = adapter.ingest_result(result)
    output = {
        "status": "ok" if ingest_result.accepted else "rejected",
        "task_updated": ingest_result.task_updated,
        "errors": ingest_result.errors,
    }
    print(json.dumps(output, ensure_ascii=False))
    return 0 if ingest_result.accepted else 2


def _cmd_change_evaluate(args: argparse.Namespace) -> int:
    path = Path(args.change_file)
    if not path.exists():
        print(json.dumps({"status": "error", "error": f"File not found: {path}"}, ensure_ascii=False))
        return 2

    with open(str(path), encoding="utf-8") as fh:
        change = json.load(fh)

    # Minimal project object for the gate engine
    from types import SimpleNamespace
    proj = SimpleNamespace()
    proj.paths = SimpleNamespace()
    proj.paths.wmb_dir = Path(args.project) / ".wmb"

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
    print(json.dumps(output, ensure_ascii=False))
    return exit_code
