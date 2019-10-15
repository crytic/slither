from slither.core.children.child_node import ChildNode
#from slither.core.variables.variable import Variable
from .variable import SlithIRVariable
from slither.core.declarations import Contract, Enum, SolidityVariable, Function


class ReferenceVariable(ChildNode, SlithIRVariable):

    def __init__(self):
        super(ReferenceVariable, self).__init__()
        self._points_to = None

    @property
    def is_scalar(self):
        return False

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
        assert is_valid_lvalue(points_to) \
               or isinstance(points_to, (SolidityVariable, Contract, Enum))

        self._points_to = points_to

