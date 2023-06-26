from typing import Optional, TYPE_CHECKING

from slither.core.declarations import Contract, Enum, SolidityVariable, Function
from slither.core.variables.variable import Variable
from slither.core.variables.top_level_variable import TopLevelVariable

if TYPE_CHECKING:
    from slither.core.cfg.node import Node


class ReferenceVariable(Variable):
    def __init__(self, node: "Node", index: Optional[int] = None) -> None:
        super().__init__()
        if index is None:
            self._index = node.compilation_unit.counter_slithir_reference
            node.compilation_unit.counter_slithir_reference += 1
        else:
            self._index = index
        self._points_to = None
        self._node = node

    @property
    def node(self) -> "Node":
        return self._node

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
        # pylint: disable=import-outside-toplevel
        from slither.slithir.utils.utils import is_valid_lvalue

        assert is_valid_lvalue(points_to) or isinstance(
            points_to, (SolidityVariable, Contract, Enum, TopLevelVariable)
        )

        self._points_to = points_to

    @property
    def points_to_origin(self):
        points = self.points_to
        while isinstance(points, ReferenceVariable):
            points = points.points_to
        return points

    @property
    def name(self) -> str:
        return f"REF_{self.index}"

    # overide of core.variables.variables
    # reference can have Function has a type
    # to handle the function selector
    def set_type(self, t) -> None:
        if not isinstance(t, Function):
            super().set_type(t)
        else:
            self._type = t

    def __str__(self) -> str:
        return self.name
