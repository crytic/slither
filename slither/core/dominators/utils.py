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

def intersection_successor(node: "Node"):
    if not node.sons:
        return set()
    ret = node.sons[0].post_dominators
    for succ in node.sons[1:]:
        ret = ret.intersection(succ.post_dominators)
    return ret


def _compute_dominators(nodes: List["Node"]):
    changed = True

    while changed:
        changed = False

        for node in nodes:
            new_set = intersection_predecessor(node).union({node})
            if new_set != node.dominators:
                node.dominators = new_set
                changed = True

def _compute_post_dominators(nodes: List["Node"]):
    changed = True

    while changed:
        changed = False

        for node in nodes:
            new_set = intersection_successor(node).union({node})
            if new_set != node.post_dominators:
                node.post_dominators = new_set
                changed = True


def _compute_immediate_dominators(nodes: List["Node"]):
    for node in nodes:
        idom_candidates = set(node.dominators)
        idom_candidates.remove(node)

        if len(idom_candidates) == 1:
            idom = idom_candidates.pop()
            node.immediate_dominator = idom
            idom.dominator_successors.add(node)
            continue

        # all_dominators contain all the dominators of all the node's dominators
        # But self inclusion is removed
        # The idom is then the only node that in idom_candidate that is not in all_dominators
        all_dominators = set()
        for d in idom_candidates:
            # optimization: if a node is already in all_dominators, then
            # its dominators are already in too
            if d in all_dominators:
                continue
            all_dominators |= d.dominators - {d}

        idom_candidates = all_dominators.symmetric_difference(idom_candidates)
        assert len(idom_candidates) <= 1
        if idom_candidates:
            idom = idom_candidates.pop()
            node.immediate_dominator = idom
            idom.dominator_successors.add(node)

def _compute_immediate_post_dominators(nodes: List["Node"]):
    for node in nodes:
        idom_candidates = set(node.post_dominators)
        idom_candidates.remove(node)

        if len(idom_candidates) == 1:
            idom = idom_candidates.pop()
            node.immediate_post_dominator = idom
            idom.post_dominator_successors.add(node)
            continue

        # all_post_dominators contain all the post dominators of all the node's post dominators
        # But self inclusion is removed
        # The idom is then the only node that in idom_candidate that is not in all_post_dominators
        all_post_dominators = set()
        for d in idom_candidates:
            # optimization: if a node is already in all_post_dominators, then
            # its post dominators are already in too
            if d in all_post_dominators:
                continue
            all_post_dominators |= d.post_dominators - {d}

        idom_candidates = all_post_dominators.symmetric_difference(idom_candidates)
        assert len(idom_candidates) <= 1
        if idom_candidates:
            idom = idom_candidates.pop()
            node.immediate_post_dominator = idom
            idom.post_dominator_successors.add(node)


def compute_dominators(nodes: List["Node"]):
    """
    Naive implementation of Cooper, Harvey, Kennedy algo
    See 'A Simple,Fast Dominance Algorithm'

    Compute strict dominators
    """

    for n in nodes:
        n.dominators = set(nodes)

    _compute_dominators(nodes)

    _compute_immediate_dominators(nodes)


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

def compute_post_dominators(nodes: List["Node"]):
    """
    Naive implementation of Cooper, Harvey, Kennedy algo
    See 'A Simple,Fast Dominance Algorithm'

    Compute strict post dominators
    """

    for n in nodes:
        n.post_dominators = set(nodes)

    _compute_post_dominators(nodes)

    _compute_immediate_post_dominators(nodes)


def compute_post_dominance_frontier(nodes: List["Node"]):
    """
    Naive implementation of Cooper, Harvey, Kennedy algo
    See 'A Simple,Fast Dominance Algorithm'

    Compute post dominance frontier
    """
    for node in nodes:
        if len(node.sons) >= 2:
            for son in node.sons:
                runner = son
                # Corner case: if there is a if without else
                # we need to add update the conditional node

                # This probably needs to be the break, assert, revert, return, throw..
                if (
                    runner == node.immediate_post_dominator
                    and runner.type == NodeType.IF
                    and node.type == NodeType.ENDIF
                ):
                    runner.post_dominance_frontier = runner.post_dominance_frontier.union({node})
                while runner != node.immediate_post_dominator:
                    runner.post_dominance_frontier = runner.post_dominance_frontier.union({node})
                    runner = runner.immediate_post_dominator