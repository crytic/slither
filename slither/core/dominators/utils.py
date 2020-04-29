from typing import List, TYPE_CHECKING

from slither.core.cfg.node import NodeType

if TYPE_CHECKING:
    from slither.core.cfg.node import Node


def intersection_predecessor(node: "Node"):
    if not node.fathers:
        return set()
    ret = node.fathers[0].dominators
    for pred in node.fathers[1:]:
        ret = ret.intersection(pred.dominators)
    return ret


def compute_dominators(nodes: List["Node"]):
    """
        Naive implementation of Cooper, Harvey, Kennedy algo
        See 'A Simple,Fast Dominance Algorithm'

        Compute strict domniators
    """
    changed = True

    for n in nodes:
        n.dominators = set(nodes)

    while changed:
        changed = False

        for node in nodes:
            new_set = intersection_predecessor(node).union({node})
            if new_set != node.dominators:
                node.dominators = new_set
                changed = True

    # compute immediate dominator
    for node in nodes:
        idom_candidates = set(node.dominators)
        idom_candidates.remove(node)

        for dominator in node.dominators:
            if dominator != node:
                [
                    idom_candidates.remove(d)
                    for d in dominator.dominators
                    if d in idom_candidates and d != dominator
                ]

        assert len(idom_candidates) <= 1
        if idom_candidates:
            idom = idom_candidates.pop()
            node.immediate_dominator = idom
            idom.dominator_successors.add(node)


def compute_dominance_frontier(nodes: List["Node"]):
    """
        Naive implementation of Cooper, Harvey, Kennedy algo
        See 'A Simple,Fast Dominance Algorithm'

        Compute dominance frontier
    """
    for node in nodes:
        if len(node.fathers) >= 2:
            for father in node.fathers:
                runner = father
                # Corner case: if there is a if without else
                # we need to add update the conditional node
                if (
                    runner == node.immediate_dominator
                    and runner.type == NodeType.IF
                    and node.type == NodeType.ENDIF
                ):
                    runner.dominance_frontier = runner.dominance_frontier.union({node})
                while runner != node.immediate_dominator:
                    runner.dominance_frontier = runner.dominance_frontier.union({node})
                    runner = runner.immediate_dominator
