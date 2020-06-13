from typing import Union, Optional, TYPE_CHECKING

from slither.core.children.child_node import ChildNode
from slither.core.declarations import Contract, Enum, SolidityVariable

from slither.slithir.variables.variable import SlithIRVariable

if TYPE_CHECKING:
    from slither.slithir.utils.utils import VALID_LVALUE


class ReferenceVariable(ChildNode, SlithIRVariable):
    def __init__(self):
        super(ReferenceVariable, self).__init__()
        self._points_to: Optional[Union["VALID_LVALUE", SolidityVariable, Contract, Enum]] = None

    @property
    def is_scalar(self) -> bool:
        return False

    @property
    def points_to(self) -> Optional[Union["VALID_LVALUE", SolidityVariable, Contract, Enum]]:
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

        assert is_valid_lvalue(points_to) or isinstance(
            points_to, (SolidityVariable, Contract, Enum)
        )

        self._points_to = points_to

    @property
    def points_to_origin(self) -> Optional[Union["VALID_LVALUE", SolidityVariable, Contract, Enum]]:
        points = self.points_to
        while isinstance(points, ReferenceVariable):
            points = points.points_to
        return points
