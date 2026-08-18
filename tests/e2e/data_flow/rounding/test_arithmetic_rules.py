"""Direct assertions for the rounding arithmetic rules.

Each test pins one rule from the roundme rule set against a minimal
fixture, so a rule regression fails the test naming that rule rather
than shifting a broad snapshot.
"""

from __future__ import annotations

from slither.analyses.data_flow.analyses.rounding.core.state import RoundingTag

from .conftest import analyze_fixture_function, finding_messages, returned_tags

UP = {RoundingTag.UP}
DOWN = {RoundingTag.DOWN}
UNKNOWN = {RoundingTag.UNKNOWN}


class TestAdditionRule:
    def test_up_plus_down_is_unknown_with_inconsistency(self) -> None:
        annotated = analyze_fixture_function(
            "Test_AdditionConflict.sol", "Test_AdditionConflict", "conflict"
        )
        assert annotated.return_tags["result"] == frozenset(UNKNOWN)
        assert any(
            "Conflicting rounding in addition: UP + DOWN" in message
            for message in finding_messages(annotated)
        )

    def test_down_plus_neutral_preserves_down(self) -> None:
        annotated = analyze_fixture_function(
            "Test_AdditionConflict.sol", "Test_AdditionConflict", "preserves"
        )
        assert annotated.return_tags["result"] == frozenset(DOWN)
        assert not finding_messages(annotated)


class TestMultiplicationRule:
    def test_up_times_down_is_unknown_with_inconsistency(self) -> None:
        annotated = analyze_fixture_function(
            "Test_MultiplicationConflict.sol",
            "Test_MultiplicationConflict",
            "conflict",
        )
        assert annotated.return_tags["result"] == frozenset(UNKNOWN)
        assert any(
            "Conflicting rounding in multiplication: UP * DOWN" in message
            for message in finding_messages(annotated)
        )

    def test_up_times_neutral_preserves_up(self) -> None:
        annotated = analyze_fixture_function(
            "Test_MultiplicationConflict.sol",
            "Test_MultiplicationConflict",
            "preserves",
        )
        assert annotated.return_tags["result"] == frozenset(UP)
        assert not finding_messages(annotated)


class TestSubtractionInversion:
    def test_neutral_minus_down_inverts_to_up(self) -> None:
        annotated = analyze_fixture_function(
            "Test_SubtractionInversion.sol",
            "Test_SubtractionInversion",
            "neutralMinusDown",
        )
        assert annotated.return_tags["result"] == frozenset(UP)

    def test_down_minus_up_agrees_as_down(self) -> None:
        annotated = analyze_fixture_function(
            "Test_SubtractionInversion.sol",
            "Test_SubtractionInversion",
            "downMinusUp",
        )
        assert annotated.return_tags["result"] == frozenset(DOWN)
        assert not finding_messages(annotated)

    def test_down_minus_down_conflicts_after_inversion(self) -> None:
        annotated = analyze_fixture_function(
            "Test_SubtractionInversion.sol",
            "Test_SubtractionInversion",
            "downMinusDown",
        )
        assert annotated.return_tags["result"] == frozenset(UNKNOWN)
        assert any(
            "Conflicting rounding in subtraction: DOWN - DOWN" in message
            for message in finding_messages(annotated)
        )


class TestDivisionFloorBias:
    def test_up_div_neutral_floor_bias_wins(self) -> None:
        annotated = analyze_fixture_function(
            "Test_DivisionFloorBias.sol", "Test_DivisionFloorBias", "upDivNeutral"
        )
        assert annotated.return_tags["result"] == frozenset(DOWN)

    def test_neutral_div_down_floor_bias_wins(self) -> None:
        annotated = analyze_fixture_function(
            "Test_DivisionFloorBias.sol", "Test_DivisionFloorBias", "neutralDivDown"
        )
        assert annotated.return_tags["result"] == frozenset(DOWN)

    def test_up_div_down_keeps_agreeing_signal(self) -> None:
        annotated = analyze_fixture_function(
            "Test_DivisionFloorBias.sol", "Test_DivisionFloorBias", "upDivDown"
        )
        assert annotated.return_tags["result"] == frozenset(UP)
        assert not finding_messages(annotated)


class TestCeilingIdiom:
    def test_canonical_ceiling_is_up(self) -> None:
        annotated = analyze_fixture_function(
            "Test_CeilingIdiom.sol", "Test_CeilingIdiom", "ceiling"
        )
        assert annotated.return_tags["result"] == frozenset(UP)
        assert not finding_messages(annotated)

    def test_near_miss_constant_is_floor_down(self) -> None:
        annotated = analyze_fixture_function(
            "Test_CeilingIdiom.sol", "Test_CeilingIdiom", "nearMissConstant"
        )
        assert annotated.return_tags["result"] == frozenset(DOWN)
        assert not finding_messages(annotated)

    def test_near_miss_divisor_is_floor_down(self) -> None:
        annotated = analyze_fixture_function(
            "Test_CeilingIdiom.sol", "Test_CeilingIdiom", "nearMissDivisor"
        )
        assert annotated.return_tags["result"] == frozenset(DOWN)
        assert not finding_messages(annotated)


def test_returned_tags_helper_sees_all_returns() -> None:
    annotated = analyze_fixture_function(
        "Test_SubtractionInversion.sol",
        "Test_SubtractionInversion",
        "downMinusUp",
    )
    assert returned_tags(annotated) == DOWN
