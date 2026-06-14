"""Finite revision-loop controller with author-confirmation support."""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any


class LoopDecision(str, enum.Enum):
    PROCEED = "proceed"
    REFINE = "refine"
    BLOCK = "block"
    AUTHOR_CONFIRMATION = "author_confirmation"


@dataclass
class LoopState:
    round: int = 0
    max_rounds: int = 3
    blocking_issues: list[str] = field(default_factory=list)
    last_blocking_reason: str | None = None
    same_blocking_count: int = 0


class LoopController:
    """Finite revision loop with material-improvement and blocking rules."""

    def __init__(self, max_rounds: int = 3) -> None:
        self._state = LoopState(max_rounds=max_rounds)

    @property
    def round(self) -> int:
        return self._state.round

    @property
    def state(self) -> LoopState:
        return self._state

    def evaluate(self, gate_result: Any, blocking_reason: str | None = None) -> LoopDecision:
        """Evaluate a single gate result and return the appropriate decision.

        Parameters
        ----------
        gate_result:
            The result from a GateEngine evaluation or equivalent.
        blocking_reason:
            If set, indicates a blocking issue that must be resolved.

        Returns
        -------
        LoopDecision:
            PROCEED, REFINE, BLOCK, or AUTHOR_CONFIRMATION.
        """
        self._state.round += 1

        # Round cap — block at max (round N >= max_rounds stops)
        if self._state.round >= self._state.max_rounds:
            return LoopDecision.BLOCK

        # Author confirmation overrides any other logic
        status = getattr(gate_result, "status", None) or getattr(gate_result, "status", "")
        if status == "awaiting_author_confirmation" or status == "awai...":
            return LoopDecision.AUTHOR_CONFIRMATION

        # Gate pass
        if blocking_reason is None:
            return LoopDecision.PROCEED

        # same blocking issue unchanged → BLOCK after two rounds
        if (
            blocking_reason == self._state.last_blocking_reason
            and blocking_reason is not None
        ):
            self._state.same_blocking_count += 1
            self._state.blocking_issues.append(blocking_reason)
            if self._state.same_blocking_count >= 1:
                return LoopDecision.BLOCK
            return LoopDecision.REFINE
        else:
            self._state.last_blocking_reason = blocking_reason
            self._state.same_blocking_count = 0
            self._state.blocking_issues.append(blocking_reason)
            return LoopDecision.REFINE

    def is_material_improvement(
        self, previous: dict[str, Any], current: dict[str, Any]
    ) -> bool:
        """Return True only if the current state reflects a material improvement
        over the previous state. Language-only edits, cosmetic changes, and
        formatting fixes are NOT material."""
        # Check for resolved blockers
        prev_blockers = set(previous.get("blocking_issues", []))
        curr_blockers = set(current.get("blocking_issues", []))
        resolved = prev_blockers - curr_blockers
        if resolved:
            return True

        # Check for reduced severity
        prev_sev = previous.get("severity", "")
        curr_sev = current.get("severity", "")
        severity_order = ["critical", "major", "minor", "cosmetic"]
        if prev_sev in severity_order and curr_sev in severity_order:
            if severity_order.index(curr_sev) > severity_order.index(prev_sev):
                return True

        # Increased trace coverage
        prev_trace = previous.get("trace_coverage", 0)
        curr_trace = current.get("trace_coverage", 0)
        if curr_trace > prev_trace:
            return True

        return False

    def reset(self) -> None:
        """Reset the loop state for a fresh revision cycle."""
        self._state = LoopState(max_rounds=self._state.max_rounds)
