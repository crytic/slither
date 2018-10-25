
from slither.core.children.child_node import ChildNode
from slither.core.declarations import Contract, Enum, SolidityVariable
from slither.core.variables.variable import Variable


class ReferenceVariable(ChildNode, Variable):

    COUNTER = 0

    def __init__(self):
        super(ReferenceVariable, self).__init__()
        self._index = ReferenceVariable.COUNTER
        ReferenceVariable.COUNTER += 1
        self._points_to = None

    @property
    def index(self):
        return self._index

    @index.setter
    def index(self, idx):
        self._index = idx

    @property
    def points_to(self):
        """
            Return the variable pointer by the reference
            It is the left member of a Index or Member operator
        """
        return self._points_to

    @points_to.setter
    def points_to(self, points_to):
        # Can only be a rvalue of
        # Member or Index operator
        from slither.slithir.utils.utils import is_valid_lvalue
        assert is_valid_lvalue(points_to) \
            or isinstance(points_to, (SolidityVariable, Contract, Enum))

        self._points_to = points_to

    @property
    def name(self):
        return 'REF_{}'.format(self.index)

    def __str__(self):
        return self.name
