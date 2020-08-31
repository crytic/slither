from typing import TYPE_CHECKING

from slither.core.children.child_node import ChildNode
from slither.slithir.variables.variable import SlithIRVariable

if TYPE_CHECKING:
    from slither.core.cfg.node import Node

from slither.core.solidity_types.type import Type


class TupleVariable(ChildNode, SlithIRVariable):

    COUNTER = 0

    def __init__(self, node: "Node", index=None):
        super(TupleVariable, self).__init__()
        if index is None:
            self._index = TupleVariable.COUNTER
            TupleVariable.COUNTER += 1
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
        return "TUPLE_{}".format(self.index)

    @name.setter
    def name(self, name):
        self._name = name

    def __str__(self):
        return self.name
