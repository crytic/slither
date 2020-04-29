"""
    Nodes of the dominator tree
"""
from typing import TYPE_CHECKING, Set, List

if TYPE_CHECKING:
    from slither.core.cfg.node import Node


class DominatorNode(object):
    def __init__(self):
        self._succ: Set["Node"] = set()
        self._nodes: List["Node"] = []

    def add_node(self, node: "Node"):
        self._nodes.append(node)

    def add_successor(self, succ: "Node"):
        self._succ.add(succ)

    @property
    def cfg_nodes(self) -> List["Node"]:
        return self._nodes

    @property
    def sucessors(self) -> Set["Node"]:
        return self._succ
