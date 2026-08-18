"""
Nodes of the dominator tree
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from slither.core.cfg.node import Node


class DominatorNode:
    def __init__(self):
        self._succ: set[Node] = set()
        self._nodes: list[Node] = []

    def add_node(self, node: "Node"):
        self._nodes.append(node)

    def add_successor(self, succ: "Node"):
        self._succ.add(succ)

    @property
    def cfg_nodes(self) -> list["Node"]:
        return self._nodes

    @property
    def sucessors(self) -> set["Node"]:
        return self._succ
