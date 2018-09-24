
from slither.core.variables.variable import Variable
from slither.core.children.child_node import ChildNode

class TemporaryVariable(ChildNode, Variable):

    COUNTER = 0

    def __init__(self):
        super(TemporaryVariable, self).__init__()
        self._index = TemporaryVariable.COUNTER
        TemporaryVariable.COUNTER += 1

    @property
    def index(self):
        return self._index

    def __str__(self):
        return 'TMP_{}'.format(self.index)
