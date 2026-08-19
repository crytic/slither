"""Regression pins for interprocedural call-summary behaviors.

Pins behaviors of the InterproceduralAnalysis migration that the rest of
the suite does not cover: the recursion guard's UNKNOWN summary trace,
tuple-call recursion as a silent no-op (not a RuntimeError), bodyless
interface calls resolving through the known-library name-only fallback,
and the nested fixpoint analyzing callees in CFG order rather than
node-list order (a soundness improvement over the old single-pass walk).
"""

from __future__ import annotations

from slither.analyses.data_flow.analyses.rounding.core.state import RoundingTag
from slither.analyses.data_flow.analyses.rounding.operations.tag_operations import (
    load_known_tags,
)

from .conftest import analyze_fixture_function, exit_tags_by_name, finding_messages


class TestScalarRecursionSummary:
    """A recursive scalar call yields {UNKNOWN} with a "returns UNKNOWN" trace."""

    def test_recursive_call_produces_returns_unknown_trace(self) -> None:
        annotated = analyze_fixture_function(
            "Test_RecursionDirect.sol", "Test_RecursionDirect", "rec"
        )
        assert annotated.return_tags["result"] == frozenset({RoundingTag.UNKNOWN})
        trace = annotated.traces["result"]
        assert trace.source == "rec() returns UNKNOWN"
        assert trace.tags == frozenset({RoundingTag.UNKNOWN})

    def test_nested_trace_carries_branch_condition(self) -> None:
        annotated = analyze_fixture_function(
            "Test_RecursionDirect.sol", "Test_RecursionDirect", "rec"
        )
        children = annotated.traces["result"].children
        assert [child.source for child in children] == ["rec() returns UNKNOWN"]
        assert children[0].branch_condition == "!(x == 0)"


class TestTupleRecursionSilentNoOp:
    """A recursive tuple call skips silently instead of raising RuntimeError."""

    def test_recursive_tuple_call_does_not_raise(self) -> None:
        annotated = analyze_fixture_function(
            "Test_TupleRecursion.sol", "Test_TupleRecursion", "bounds"
        )
        tags = exit_tags_by_name(annotated)
        assert tags["lo"] == {RoundingTag.DOWN}
        assert tags["hi"] == {RoundingTag.UP}

    def test_caller_gets_base_case_per_index_tags(self) -> None:
        annotated = analyze_fixture_function(
            "Test_TupleRecursion.sol", "Test_TupleRecursion", "caller"
        )
        tags = exit_tags_by_name(annotated)
        assert tags["l"] == {RoundingTag.DOWN}
        assert tags["h"] == {RoundingTag.UP}


class TestBodylessInterfaceCall:
    """Interface targets resolve via the name-only known-library fallback."""

    def test_known_table_name_fallback_tags_interface_call(self) -> None:
        annotated = analyze_fixture_function(
            "Test_InterfaceKnownLib.sol",
            "Test_InterfaceKnownLib",
            "caller",
            known_tags=load_known_tags(),
        )
        assert annotated.return_tags["result"] == frozenset({RoundingTag.DOWN})
        assert annotated.traces["result"].source == "mulDiv() → DOWN (known library)"

    def test_without_table_bodyless_target_defaults_to_neutral(self) -> None:
        annotated = analyze_fixture_function(
            "Test_InterfaceKnownLib.sol", "Test_InterfaceKnownLib", "caller"
        )
        assert annotated.return_tags["result"] == frozenset({RoundingTag.NEUTRAL})


class TestCalleeNodeOrderIndependence:
    """The nested fixpoint analyzes callees in CFG order, not node-list order.

    Slither lists a do-while's IFLOOP condition node before the loop-body
    node it depends on. The old single-pass callee walk evaluated the
    condition with the body's tags still unset and missed the both-DOWN
    division below; the nested engine propagates DOWN into the condition
    and reports it.
    """

    def test_do_while_condition_sees_loop_body_tags(self) -> None:
        annotated = analyze_fixture_function(
            "Test_DoWhileCallee.sol", "Test_DoWhileCallee", "caller"
        )
        assert annotated.return_tags["result"] == frozenset({RoundingTag.DOWN})
        assert any(
            "Division rounding inconsistency in helper: "
            "numerator and denominator both DOWN" in message
            for message in finding_messages(annotated)
        )
