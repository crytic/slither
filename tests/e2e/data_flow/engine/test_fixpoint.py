"""Worklist/fixpoint edge-case tests for the data-flow engine.

Each fixture contract exercises exactly one CFG shape: minimal graph,
unreachable code, a loop needing the widening hook, and a diamond merge
with conflicting tags.
"""

from __future__ import annotations

from pathlib import Path

from slither import Slither
from slither.analyses.data_flow.analyses.rounding.analysis.analysis import (
    RoundingAnalysis,
)
from slither.analyses.data_flow.analyses.rounding.analysis.domain import (
    DomainVariant,
)
from slither.analyses.data_flow.analyses.rounding.core.state import (
    RoundingTag,
)
from slither.analyses.data_flow.engine.domain import Domain
from slither.analyses.data_flow.engine.engine import Engine
from slither.core.cfg.node import NodeType
from slither.core.declarations.function import Function

CONTRACTS_DIR = Path(__file__).parent / "contracts"


def _function(contract_file: str, function_name: str) -> Function:
    slither = Slither(str(CONTRACTS_DIR / contract_file))
    return next(
        function
        for contract in slither.contracts
        for function in contract.functions_declared
        if function.name == function_name
    )


def _run(function: Function, analysis: RoundingAnalysis | None = None) -> Engine:
    engine = Engine.new(analysis or RoundingAnalysis(), function)
    engine.run_analysis()
    return engine


class WideningProbe(RoundingAnalysis):
    """RoundingAnalysis instrumented to count widening-hook invocations."""

    def __init__(self) -> None:
        super().__init__()
        self.widening_calls = 0

    def apply_widening(
        self,
        current_state: Domain,
        previous_state: Domain,
        widening_thresholds: set[int],
    ) -> Domain:
        self.widening_calls += 1
        return super().apply_widening(
            current_state, previous_state, widening_thresholds
        )


def test_minimal_function_reaches_fixpoint_in_one_pass() -> None:
    function = _function("EngineNoop.sol", "noop")
    engine = _run(function)

    result = engine.result()
    assert len(result) == len(function.nodes)
    assert engine.iteration_count == len(function.nodes)
    entry_state = result[function.entry_point]
    assert entry_state.post.variant == DomainVariant.STATE


def test_unreachable_nodes_stay_at_bottom() -> None:
    function = _function("EngineUnreachable.sol", "unreachable")
    engine = _run(function)

    unreachable_nodes = [
        node
        for node in function.nodes
        if node.type is not NodeType.ENTRYPOINT and not node.fathers
    ]
    assert unreachable_nodes, "fixture must contain unreachable nodes"

    result = engine.result()
    for node in unreachable_nodes:
        state = result[node]
        assert state.pre.variant == DomainVariant.BOTTOM
        assert state.post.variant == DomainVariant.BOTTOM


def test_loop_converges_and_invokes_widening_hook() -> None:
    function = _function("EngineLoop.sol", "loop")
    probe = WideningProbe()
    engine = _run(function, analysis=probe)

    assert engine.iteration_count < 100, "loop should converge quickly"
    assert probe.widening_calls > 0, "IFLOOP successor must trigger widening"

    exit_states = [
        state for node, state in engine.result().items() if not node.sons
    ]
    assert exit_states
    for state in exit_states:
        assert state.post.variant == DomainVariant.STATE


def test_diamond_merge_joins_conflicting_tags() -> None:
    function = _function("EngineDiamond.sol", "diamond")
    engine = _run(function)

    exit_states = [
        state for node, state in engine.result().items() if not node.sons
    ]
    assert exit_states

    merged: set[RoundingTag] = set()
    for state in exit_states:
        assert state.post.variant == DomainVariant.STATE
        for variable, tags in state.post.state._tags.items():
            if variable.name == "r":
                merged.update(tags)

    assert RoundingTag.UP in merged, "true-branch tag lost at merge"
    assert RoundingTag.DOWN in merged, "false-branch tag lost at merge"
