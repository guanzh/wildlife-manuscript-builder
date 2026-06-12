"""Minimal command-line surface for Wildlife Manuscript Builder."""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from wmb import __version__


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
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the minimal WMB command-line interface."""

    try:
        _parser().parse_args(argv)
    except SystemExit as exc:
        return int(exc.code)
    return 0
