from .variable import SlithIRVariable
from slither.core.variables.variable import Variable
from slither.core.children.child_node import ChildNode

from slither.core.solidity_types.type import Type
class TupleVariable(ChildNode, SlithIRVariable):

    COUNTER = 0

    def __init__(self, node, index=None):
        super(TupleVariable, self).__init__()
        if index is None:
            self._index = TupleVariable.COUNTER
            TupleVariable.COUNTER += 1
        else:
            self._index = index

        self._node = node

    @property
    def index(self):
        return self._index

    @index.setter
    def index(self, idx):
        self._index = idx

    @property
    def name(self):
        return 'TUPLE_{}'.format(self.index)

    def __str__(self):
        return self.name
