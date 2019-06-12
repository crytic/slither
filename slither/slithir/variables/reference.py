from .variable import SlithIRVariable
from slither.core.children.child_node import ChildNode
from slither.core.variables.variable import Variable
from slither.core.declarations import Contract, Enum, SolidityVariable, Function


class ReferenceVariable(ChildNode, Variable):

    COUNTER = 0

    def __init__(self, node, index=None):
        super(ReferenceVariable, self).__init__()
        if index is None:
            self._index = ReferenceVariable.COUNTER
            ReferenceVariable.COUNTER += 1
        else:
            self._index = index
        self._points_to = None
        self._node = node

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

    @property
    def points_to_origin(self):
        points = self.points_to
        while isinstance(points, ReferenceVariable):
            points = points.points_to
        return points

    @points_to.setter
    def points_to(self, points_to):
        # Can only be a rvalue of
        # Member or Index operator
        from slither.slithir.utils.utils import is_valid_lvalue

        assert is_valid_lvalue(points_to) or isinstance(
            points_to, (SolidityVariable, Contract, Enum)
        )

        self._points_to = points_to

    @property
    def name(self):
        return "REF_{}".format(self.index)

    # overide of core.variables.variables
    # reference can have Function has a type
    # to handle the function selector
    def set_type(self, t):
        if not isinstance(t, Function):
            super(ReferenceVariable, self).set_type(t)
        else:
            self._type = t

    def __str__(self):
        return self.name
