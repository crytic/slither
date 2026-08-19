"""CFG branch-condition helpers for data flow analyses.

Formats the IF condition guarding a CFG node as a display string, using
pure dominator-tree logic.

Placement: consumers are data-flow analyses that need trace/provenance
display (e.g. annotating which branch a return value came from), and the
logic depends only on ``slither.core.cfg`` — so the engine layer is the
lowest layer where all intended consumers live. It does not belong in
``slither/core`` because it formats conditions as display strings, an
analysis-layer concern.
"""

from __future__ import annotations

from slither.core.cfg.node import Node, NodeType


def find_branch_condition(node: Node) -> str | None:
    """Find the IF condition guarding a CFG node, if any.

    Walks up the immediate-dominator chain. When an IF node is found,
    determines whether the original node is in the true or false branch
    by checking which son dominates it.

    Args:
        node: The CFG node whose guarding condition to look up.

    Returns:
        The condition expression as a string (negated with ``!(...)``
        for the false branch), or None if the node is unguarded.
    """
    current = node
    while current.immediate_dominator is not None:
        idom = current.immediate_dominator
        if idom.type is NodeType.IF and idom.expression is not None:
            if is_in_true_branch(idom, node):
                return str(idom.expression)
            if is_in_false_branch(idom, node):
                return f"!({idom.expression})"
            break
        current = idom
    return None


def is_in_true_branch(if_node: Node, target: Node) -> bool:
    """Check if target is dominated by the true branch of if_node.

    Args:
        if_node: The IF node whose true branch to test against.
        target: The node whose position is being checked.

    Returns:
        True if target is (or is dominated by) the true-branch son.
    """
    son_true = if_node.son_true
    if son_true is None:
        return False
    return son_true == target or son_true in target.dominators


def is_in_false_branch(if_node: Node, target: Node) -> bool:
    """Check if target is dominated by the false branch of if_node.

    Args:
        if_node: The IF node whose false branch to test against.
        target: The node whose position is being checked.

    Returns:
        True if target is (or is dominated by) the false-branch son.
    """
    son_false = if_node.son_false
    if son_false is None:
        return False
    return son_false == target or son_false in target.dominators
