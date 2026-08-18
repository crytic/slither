"""Tuple-return and split-direction assertions.

Covers per-index Unpack matching for three-value tuples (including a
skipped element) and the split-direction rule on named return values.
"""

from __future__ import annotations

from slither.analyses.data_flow.analyses.rounding.core.state import RoundingTag

from .conftest import analyze_fixture_function, exit_tags_by_name, finding_messages


class TestTupleUnpackByIndex:
    def test_three_way_destructure_maps_each_index(self) -> None:
        annotated = analyze_fixture_function(
            "Test_TupleThree.sol", "Test_TupleThree", "destructureAll"
        )
        tags = exit_tags_by_name(annotated)
        assert tags["l"] == {RoundingTag.DOWN}
        assert tags["m"] == {RoundingTag.NEUTRAL}
        assert tags["h"] == {RoundingTag.UP}

    def test_skipped_middle_element_keeps_index_alignment(self) -> None:
        annotated = analyze_fixture_function(
            "Test_TupleThree.sol", "Test_TupleThree", "skipMiddle"
        )
        tags = exit_tags_by_name(annotated)
        assert tags["l"] == {RoundingTag.DOWN}
        assert tags["h"] == {RoundingTag.UP}


class TestSplitDirectionNamedReturns:
    def test_disagreeing_named_returns_are_flagged(self) -> None:
        annotated = analyze_fixture_function(
            "Test_SplitNamedReturns.sol", "Test_SplitNamedReturns", "split"
        )
        assert annotated.return_tags["down"] == frozenset({RoundingTag.DOWN})
        assert annotated.return_tags["up"] == frozenset({RoundingTag.UP})
        assert any(
            "Split-direction return in split" in message
            for message in finding_messages(annotated)
        )

    def test_agreeing_named_returns_are_not_flagged(self) -> None:
        annotated = analyze_fixture_function(
            "Test_SplitNamedReturns.sol", "Test_SplitNamedReturns", "aligned"
        )
        assert not any(
            "Split-direction return" in message
            for message in finding_messages(annotated)
        )
