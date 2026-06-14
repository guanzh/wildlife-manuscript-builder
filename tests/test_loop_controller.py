"""Tests for LoopController and finite revision loop."""

from __future__ import annotations

import pytest

from wmb.core.loop_controller import LoopController, LoopDecision


class _FakeGateResult:
    """Lightweight gate result that supports .status access."""

    def __init__(self, status: str) -> None:
        self.status = status


def test_loop_proceeds_when_blockers_resolved() -> None:
    ctrl = LoopController(max_rounds=3)
    ctrl.evaluate(_FakeGateResult("pass"), blocking_reason="issue A")
    decision = ctrl.evaluate(_FakeGateResult("pass"), blocking_reason=None)
    assert decision == LoopDecision.PROCEED


def test_loop_blocks_after_same_blocker_twice() -> None:
    ctrl = LoopController(max_rounds=3)
    ctrl.evaluate(_FakeGateResult("fail"), blocking_reason="stuck")
    decision = ctrl.evaluate(_FakeGateResult("fail"), blocking_reason="stuck")
    assert decision == LoopDecision.BLOCK


def test_loop_blocks_at_round_three() -> None:
    ctrl = LoopController(max_rounds=2)
    ctrl.evaluate(_FakeGateResult("fail"), blocking_reason="issue")
    ctrl.evaluate(_FakeGateResult("fail"), blocking_reason="issue B")
    decision = ctrl.evaluate(_FakeGateResult("fail"), blocking_reason="issue C")
    assert decision == LoopDecision.BLOCK


def test_author_trigger_interrupts_loop() -> None:
    ctrl = LoopController(max_rounds=3)
    decision = ctrl.evaluate(
        _FakeGateResult("awaiting_author_confirmation"),
        blocking_reason=None,
    )
    assert decision == LoopDecision.AUTHOR_CONFIRMATION


def test_round_increments_on_each_call() -> None:
    ctrl = LoopController(max_rounds=3)
    assert ctrl.round == 0
    ctrl.evaluate(_FakeGateResult("pass"), blocking_reason=None)
    assert ctrl.round == 1
    ctrl.evaluate(_FakeGateResult("pass"), blocking_reason="x")
    assert ctrl.round == 2


def test_reset_clears_state() -> None:
    ctrl = LoopController(max_rounds=3)
    ctrl.evaluate(_FakeGateResult("fail"), blocking_reason="err")
    # second call with same reason blocks immediately with fixed logic
    decision = ctrl.evaluate(_FakeGateResult("fail"), blocking_reason="err")
    assert decision == LoopDecision.BLOCK
    ctrl.reset()
    assert ctrl.round == 0
    assert ctrl.state.same_blocking_count == 0


def test_new_blocking_reason_resets_same_blocking_counter() -> None:
    ctrl = LoopController(max_rounds=5)
    ctrl.evaluate(_FakeGateResult("fail"), blocking_reason="A")
    assert ctrl.state.same_blocking_count == 0  # first occurrence → BLOCK
    ctrl.evaluate(_FakeGateResult("fail"), blocking_reason="B")  # new reason, reset
    assert ctrl.state.same_blocking_count == 0


def test_max_rounds_3_blocks_on_round_3() -> None:
    """R5: max_rounds=3, round 3 must BLOCK even with progress."""
    ctrl = LoopController(max_rounds=3)
    ctrl.evaluate(_FakeGateResult("fail"), blocking_reason="A")
    ctrl.evaluate(_FakeGateResult("fail"), blocking_reason="B")
    decision = ctrl.evaluate(_FakeGateResult("fail"), blocking_reason="C")
    assert decision == LoopDecision.BLOCK  # round 3 >= max_rounds=3


def test_material_improvement_resolved_blocker() -> None:
    ctrl = LoopController(max_rounds=3)
    prev = {"blocking_issues": ["stuck"], "severity": "critical", "trace_coverage": 0}
    curr = {"blocking_issues": [], "severity": "critical", "trace_coverage": 0}
    assert ctrl.is_material_improvement(prev, curr) is True


def test_material_improvement_reduced_severity() -> None:
    ctrl = LoopController(max_rounds=3)
    prev = {"blocking_issues": ["x"], "severity": "major", "trace_coverage": 5}
    curr = {"blocking_issues": ["x"], "severity": "minor", "trace_coverage": 5}
    assert ctrl.is_material_improvement(prev, curr) is True


def test_material_improvement_increased_trace() -> None:
    ctrl = LoopController(max_rounds=3)
    prev = {"blocking_issues": ["x"], "severity": "major", "trace_coverage": 3}
    curr = {"blocking_issues": ["x"], "severity": "major", "trace_coverage": 7}
    assert ctrl.is_material_improvement(prev, curr) is True


def test_language_only_not_material() -> None:
    ctrl = LoopController(max_rounds=3)
    prev = {"blocking_issues": [], "severity": "cosmetic", "trace_coverage": 5}
    curr = {"blocking_issues": [], "severity": "cosmetic", "trace_coverage": 5}
    assert ctrl.is_material_improvement(prev, curr) is False
