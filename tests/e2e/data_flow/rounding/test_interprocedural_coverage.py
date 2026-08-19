"""Coverage pins for interprocedural corner cases found in the final sweep.

Pins four behaviors the rest of the suite does not cover: multi-tag
arguments collapsing to UNKNOWN when bound into a callee, the call
depth cap degrading a long real call chain to UNKNOWN (instead of a
RecursionError), findings raised two call levels deep attributing to
the outermost call site, and an unreachable Return node in a callee
being read from bottom state without diluting the summary.
"""

from __future__ import annotations

from slither.analyses.data_flow.analyses.rounding.core.models import get_node_line
from slither.analyses.data_flow.analyses.rounding.core.state import RoundingTag
from slither.analyses.data_flow.engine.interprocedural import InterproceduralAnalysis

from .conftest import CONTRACTS_DIR, analyze_fixture_function


def _fixture_line_of(contract_file: str, marker: str) -> int:
    """1-based line number of the unique source line containing ``marker``."""
    source = (CONTRACTS_DIR / contract_file).read_text().splitlines()
    matches = [index for index, line in enumerate(source, start=1) if marker in line]
    assert len(matches) == 1, f"marker {marker!r} must be unique in {contract_file}"
    return matches[0]


class TestMultiTagArgumentCollapse:
    """A {DOWN, UP} argument collapses to a single UNKNOWN tag in the callee.

    ``bind_arguments`` seeds callee parameters via ``get_variable_tag``,
    whose len>1 collapse turns the split-return {DOWN, UP} result into
    UNKNOWN before the passthrough helper's body is analyzed.
    """

    def test_split_return_result_passed_to_helper_is_unknown(self) -> None:
        annotated = analyze_fixture_function(
            "Test_MultiTagArgument.sol", "Test_MultiTagArgument", "twoStep"
        )
        assert annotated.return_tags["result"] == frozenset({RoundingTag.UNKNOWN})


class TestCallDepthCap:
    """A call chain deeper than the cap degrades to UNKNOWN, not RecursionError."""

    def test_deep_chain_completes_and_degrades_to_unknown(self) -> None:
        source = (CONTRACTS_DIR / "Test_DeepCallChain.sol").read_text()
        chain_length = source.count("function f")
        # Sizing only: the fixture chain must outreach the cap for the
        # UNKNOWN assertion below to exercise the depth-cap path.
        assert chain_length > InterproceduralAnalysis._MAX_CALL_DEPTH

        annotated = analyze_fixture_function(
            "Test_DeepCallChain.sol", "Test_DeepCallChain", "entry"
        )
        assert annotated.return_tags["result"] == frozenset({RoundingTag.UNKNOWN})


class TestNestedFindingAttribution:
    """A finding raised two call levels deep attributes to the OUTERMOST site.

    entry() calls mid() calls conflicting(); the both-DOWN division in
    conflicting() must be reported at entry()'s call to mid(), not at
    mid()'s internal call to conflicting().
    """

    def test_finding_attributes_to_entry_call_site(self) -> None:
        entry_call_line = _fixture_line_of("Test_NestedFindingSite.sol", "mid(w, x, y, z)")
        mid_call_line = _fixture_line_of("Test_NestedFindingSite.sol", "conflicting(a, b, c, d);")
        annotated = analyze_fixture_function(
            "Test_NestedFindingSite.sol", "Test_NestedFindingSite", "entry"
        )
        lines = [
            get_node_line(finding.node)
            for finding in annotated.inconsistencies
            if "Division rounding inconsistency" in finding.message
        ]
        assert lines == [entry_call_line]
        assert mid_call_line not in lines


class TestUnreachableCalleeReturn:
    """An unreachable Return in a callee does not dilute the call summary.

    The callee's second ``return b;`` node is never visited, so its
    post state stays bottom; the summary reads NEUTRAL from it and the
    NEUTRAL-absorption keeps the reachable return's DOWN undiluted.
    """

    def test_caller_keeps_reachable_return_tag(self) -> None:
        annotated = analyze_fixture_function(
            "Test_UnreachableReturn.sol", "Test_UnreachableReturn", "caller"
        )
        assert annotated.return_tags["result"] == frozenset({RoundingTag.DOWN})
