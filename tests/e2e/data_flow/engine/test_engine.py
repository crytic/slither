"""Tests for the data-flow engine's state handling.

Uses RoundingAnalysis as the concrete analysis, since it is the only
Analysis implementation; the assertions target engine semantics
(pre/post separation, entry-domain seeding), not rounding rules.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from slither import Slither
from slither.analyses.data_flow.analyses.rounding.analysis.analysis import (
    RoundingAnalysis,
)
from slither.analyses.data_flow.analyses.rounding.analysis.domain import (
    DomainVariant,
    RoundingDomain,
)
from slither.analyses.data_flow.analyses.rounding.core.state import (
    RoundingTag,
)
from slither.analyses.data_flow.engine.engine import Engine
from slither.core.declarations.function import Function

CONTRACT_PATH = Path(__file__).parent / "contracts" / "EngineFixture.sol"

UP = frozenset({RoundingTag.UP})
NEUTRAL = frozenset({RoundingTag.NEUTRAL})


@pytest.fixture(scope="module")
def fixture_function() -> Function:
    """Compile the fixture contract and return its `add` function."""
    slither = Slither(str(CONTRACT_PATH))
    return next(
        function
        for contract in slither.contracts
        for function in contract.functions_declared
        if function.name == "add"
    )


def _run_engine(
    function: Function,
    entry_domain: RoundingDomain | None = None,
) -> Engine:
    engine = Engine.new(RoundingAnalysis(), function, entry_domain=entry_domain)
    engine.run_analysis()
    return engine


def _seeded_domain(function: Function) -> RoundingDomain:
    domain = RoundingDomain(DomainVariant.STATE)
    domain.state.set_tag(function.parameters[0], RoundingTag.UP)
    return domain


def test_pre_and_post_are_independent_objects(fixture_function: Function) -> None:
    """Transfer functions must not mutate the stored pre-state."""
    engine = _run_engine(fixture_function)

    entry_point = fixture_function.entry_point
    for node, state in engine.result().items():
        assert state.pre is not state.post, f"pre/post aliased at node {node.node_id}"
        if node is entry_point:
            # The entry node has no predecessors, so its pre-state must
            # still be the untouched initial bottom value after the run.
            assert state.pre.variant == DomainVariant.BOTTOM
            assert state.post.variant == DomainVariant.STATE


def test_unseeded_entry_defaults_to_neutral(fixture_function: Function) -> None:
    engine = _run_engine(fixture_function)

    entry_state = engine.result()[fixture_function.entry_point]
    for parameter in fixture_function.parameters:
        assert entry_state.post.state.get_tags(parameter) == NEUTRAL


def test_entry_domain_seeds_entry_state(fixture_function: Function) -> None:
    """Seeded tags survive entry initialization; absent ones still default."""
    seeded_param, unseeded_param = fixture_function.parameters
    engine = _run_engine(fixture_function, entry_domain=_seeded_domain(fixture_function))

    result = engine.result()
    entry_state = result[fixture_function.entry_point]
    assert entry_state.pre.variant == DomainVariant.STATE
    assert entry_state.post.state.get_tags(seeded_param) == UP
    assert entry_state.post.state.get_tags(unseeded_param) == NEUTRAL

    exit_states = [
        state for node, state in result.items() if not node.sons
    ]
    assert exit_states, "fixture function must have an exit node"
    for state in exit_states:
        assert state.post.state.get_tags(seeded_param) == UP


def test_entry_domain_is_not_mutated_by_engine(fixture_function: Function) -> None:
    """The engine copies the seed instead of taking ownership of it."""
    seeded_param, unseeded_param = fixture_function.parameters
    entry_domain = _seeded_domain(fixture_function)
    _run_engine(fixture_function, entry_domain=entry_domain)

    assert entry_domain.state.get_tags(seeded_param) == UP
    assert not entry_domain.state.has_tag(unseeded_param)


def test_seeding_does_not_leak_between_engine_runs(
    fixture_function: Function,
) -> None:
    """A seeded run must not contaminate a later unseeded run."""
    seeded_param = fixture_function.parameters[0]
    _run_engine(fixture_function, entry_domain=_seeded_domain(fixture_function))

    unseeded_engine = _run_engine(fixture_function)
    entry_state = unseeded_engine.result()[fixture_function.entry_point]
    assert entry_state.pre.variant == DomainVariant.BOTTOM
    assert entry_state.post.state.get_tags(seeded_param) == NEUTRAL


def test_same_seed_object_reusable_across_runs(fixture_function: Function) -> None:
    """Reusing one entry_domain for two runs gives identical results."""
    seeded_param = fixture_function.parameters[0]
    entry_domain = _seeded_domain(fixture_function)

    first = _run_engine(fixture_function, entry_domain=entry_domain)
    second = _run_engine(fixture_function, entry_domain=entry_domain)

    for engine in (first, second):
        entry_state = engine.result()[fixture_function.entry_point]
        assert entry_state.post.state.get_tags(seeded_param) == UP
    assert entry_domain.state.get_tags(seeded_param) == UP
