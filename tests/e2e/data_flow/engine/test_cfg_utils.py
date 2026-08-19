"""End-to-end tests for the CFG branch-condition helpers.

Compiles a small fixture so the helpers run against real dominator
trees: a diamond if/else (true branch, false branch, join node) and a
straight-line function with no IF at all.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from slither import Slither
from slither.analyses.data_flow.engine.cfg_utils import (
    find_branch_condition,
    is_in_false_branch,
    is_in_true_branch,
)
from slither.core.cfg.node import Node, NodeType
from slither.core.declarations.function import Function

CONTRACTS_DIR = Path(__file__).parent / "contracts"


@pytest.fixture(scope="module")
def functions() -> dict[str, Function]:
    """Compile the fixture and index its functions by name."""
    slither = Slither(str(CONTRACTS_DIR / "EngineBranch.sol"))
    return {
        function.name: function
        for contract in slither.contracts
        for function in contract.functions_declared
    }


def _if_node(function: Function) -> Node:
    return next(node for node in function.nodes if node.type is NodeType.IF)


def _deeper(node: Node) -> Node:
    """The single successor of a branch's first statement node."""
    assert len(node.sons) == 1
    return node.sons[0]


def test_true_branch_returns_condition(functions: dict[str, Function]) -> None:
    if_node = _if_node(functions["pick"])

    assert find_branch_condition(if_node.son_true) == "roundUp"


def test_node_dominated_by_true_branch_returns_condition(
    functions: dict[str, Function],
) -> None:
    """The dominator walk must climb past intermediate statement nodes."""
    if_node = _if_node(functions["pick"])

    assert find_branch_condition(_deeper(if_node.son_true)) == "roundUp"


def test_false_branch_returns_negated_condition(functions: dict[str, Function]) -> None:
    if_node = _if_node(functions["pick"])

    assert find_branch_condition(if_node.son_false) == "!(roundUp)"
    assert find_branch_condition(_deeper(if_node.son_false)) == "!(roundUp)"


def test_join_node_after_if_is_unguarded(functions: dict[str, Function]) -> None:
    """The join is dominated by the IF itself but by neither branch."""
    pick = functions["pick"]
    end_if = next(node for node in pick.nodes if node.type is NodeType.ENDIF)
    return_node = next(node for node in pick.nodes if node.type is NodeType.RETURN)

    assert find_branch_condition(end_if) is None
    assert find_branch_condition(return_node) is None


def test_function_without_if_is_unguarded(functions: dict[str, Function]) -> None:
    straight = functions["straight"]

    assert all(find_branch_condition(node) is None for node in straight.nodes)


def test_branch_membership_predicates(functions: dict[str, Function]) -> None:
    pick = functions["pick"]
    if_node = _if_node(pick)
    end_if = next(node for node in pick.nodes if node.type is NodeType.ENDIF)

    assert is_in_true_branch(if_node, if_node.son_true) is True
    assert is_in_true_branch(if_node, _deeper(if_node.son_true)) is True
    assert is_in_true_branch(if_node, if_node.son_false) is False
    assert is_in_true_branch(if_node, end_if) is False

    assert is_in_false_branch(if_node, if_node.son_false) is True
    assert is_in_false_branch(if_node, _deeper(if_node.son_false)) is True
    assert is_in_false_branch(if_node, if_node.son_true) is False
    assert is_in_false_branch(if_node, end_if) is False
