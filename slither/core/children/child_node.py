from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from slither import Slither
    from slither.core.cfg.node import Node
    from slither.core.declarations import Function, Contract


class ChildNode:
    def __init__(self):
        super(ChildNode, self).__init__()
        self._node = None

    def set_node(self, node: "Node"):
        self._node = node

    @property
    def node(self) -> "Node":
        return self._node

    @property
    def function(self) -> "Function":
        return self.node.function

    @property
    def contract(self) -> "Contract":
        return self.node.function.contract

    @property
    def slither(self) -> "Slither":
        return self.contract.slither
