from typing import TYPE_CHECKING

from slither.core.children.child_node import ChildNode
from slither.core.declarations import Contract, Enum, SolidityVariable, Function
from slither.core.variables.variable import Variable

if TYPE_CHECKING:
    from slither.core.cfg.node import Node


class ReferenceVariable(ChildNode, Variable):
    def __init__(self, node: "Node", index=None):
        super().__init__()
        if index is None:
            self._index = node.compilation_unit.counter_slithir_reference
            node.compilation_unit.counter_slithir_reference += 1
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
        # pylint: disable=import-outside-toplevel
        from slither.slithir.utils.utils import is_valid_lvalue

        assert is_valid_lvalue(points_to) or isinstance(
            points_to, (SolidityVariable, Contract, Enum)
        )

        self._points_to = points_to

    @property
    def name(self):
        return f"REF_{self.index}"

    # overide of core.variables.variables
    # reference can have Function has a type
    # to handle the function selector
    def set_type(self, t):
        if not isinstance(t, Function):
            super().set_type(t)
        else:
            self._type = t

    def __str__(self):
        return self.name
