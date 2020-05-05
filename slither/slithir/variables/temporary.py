from typing import TYPE_CHECKING, Optional

from slither.core.children.child_node import ChildNode
from slither.core.variables.variable import Variable

if TYPE_CHECKING:
    from slither.core.cfg.node import Node


class TemporaryVariable(ChildNode, Variable):
    COUNTER = 0

    def __init__(self, node: "Node", index: Optional[int] = None):
        super(TemporaryVariable, self).__init__()
        if index is None:
            self._index = TemporaryVariable.COUNTER
            TemporaryVariable.COUNTER += 1
        else:
            self._index = index
        self._node: "Node" = node

    @property
    def index(self) -> int:
        return self._index

    @index.setter
    def index(self, idx):
        self._index = idx

    @property
    def name(self) -> str:
        return "TMP_{}".format(self.index)

    @name.setter
    def name(self, name):
        self._name = name

    def __str__(self):
        return self.name
