"""Interprocedural resolution assertions.

One test per rung of the call-resolution ladder (inline annotation,
name allowlist, known-library table, body analysis), plus the recursion
guard, findings dedup, and variable-suffix annotation mismatches.
"""

from __future__ import annotations

from slither.analyses.data_flow.analyses.rounding.core.state import RoundingTag
from slither.analyses.data_flow.analyses.rounding.operations.tag_operations import (
    load_known_tags,
)

from .conftest import analyze_fixture_function, finding_messages


class TestResolutionLadder:
    def test_rung1_inline_annotation_beats_name_inference(self) -> None:
        annotated = analyze_fixture_function(
            "Test_LadderInline.sol", "Test_LadderInline", "annotated"
        )
        assert annotated.return_tags["result"] == frozenset({RoundingTag.DOWN})

    def test_rung2_name_allowlist_beats_body_analysis(self) -> None:
        annotated = analyze_fixture_function(
            "Test_LadderInline.sol", "Test_LadderInline", "unannotated"
        )
        assert annotated.return_tags["result"] == frozenset({RoundingTag.UP})

        annotated = analyze_fixture_function(
            "Test_LadderName.sol", "Test_LadderName", "caller"
        )
        assert annotated.return_tags["result"] == frozenset({RoundingTag.UP})

    def test_rung3_known_library_table_beats_body_analysis(self) -> None:
        annotated = analyze_fixture_function(
            "Test_LadderKnownLib.sol",
            "Test_LadderKnownLib",
            "caller",
            known_tags=load_known_tags(),
        )
        assert annotated.return_tags["result"] == frozenset({RoundingTag.DOWN})

    def test_rung4_body_analysis_when_no_table_loaded(self) -> None:
        annotated = analyze_fixture_function(
            "Test_LadderKnownLib.sol", "Test_LadderKnownLib", "caller"
        )
        assert annotated.return_tags["result"] == frozenset({RoundingTag.UP})

    def test_rung4_body_analysis_fallthrough(self) -> None:
        annotated = analyze_fixture_function(
            "Test_LadderBody.sol", "Test_LadderBody", "caller"
        )
        assert annotated.return_tags["result"] == frozenset({RoundingTag.DOWN})


class TestRecursionGuard:
    def test_direct_recursion_returns_unknown(self) -> None:
        annotated = analyze_fixture_function(
            "Test_RecursionDirect.sol", "Test_RecursionDirect", "rec"
        )
        assert annotated.return_tags["result"] == frozenset({RoundingTag.UNKNOWN})

    def test_mutual_recursion_returns_unknown(self) -> None:
        annotated = analyze_fixture_function(
            "Test_RecursionMutual.sol", "Test_RecursionMutual", "a"
        )
        assert annotated.return_tags["result"] == frozenset({RoundingTag.UNKNOWN})


class TestFindingsDedup:
    @staticmethod
    def _division_findings(annotated) -> list[str]:
        return [
            message
            for message in finding_messages(annotated)
            if "Division rounding inconsistency" in message
        ]

    def test_two_calls_on_one_line_report_once(self) -> None:
        annotated = analyze_fixture_function(
            "Test_FindingsDedup.sol", "Test_FindingsDedup", "sameLine"
        )
        assert len(self._division_findings(annotated)) == 1

    def test_two_calls_on_separate_lines_report_each_site(self) -> None:
        annotated = analyze_fixture_function(
            "Test_FindingsDedup.sol", "Test_FindingsDedup", "twoLines"
        )
        assert len(self._division_findings(annotated)) == 2


class TestAnnotationMismatch:
    def test_suffix_contradicting_inference_is_flagged(self) -> None:
        annotated = analyze_fixture_function(
            "Test_AnnotationMismatch.sol", "Test_AnnotationMismatch", "mismatch"
        )
        assert any(
            "expected DOWN but inferred UP" in finding.message
            for finding in annotated.annotation_mismatches
        )

    def test_suffix_matching_inference_is_not_flagged(self) -> None:
        annotated = analyze_fixture_function(
            "Test_AnnotationMismatch.sol", "Test_AnnotationMismatch", "matching"
        )
        assert not annotated.annotation_mismatches
