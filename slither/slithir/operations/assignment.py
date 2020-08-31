import logging
from typing import List, TYPE_CHECKING, Union

from slither.core.declarations.function import Function
from slither.slithir.operations.lvalue import OperationWithLValue
from slither.slithir.utils.utils import is_valid_lvalue, is_valid_rvalue
from slither.slithir.variables import IndexVariable
from slither.slithir.variables import TupleVariable

if TYPE_CHECKING:
    from slither.slithir.utils.utils import VALID_RVALUE, VALID_LVALUE
    from slither.core.solidity_types.type import Type

logger = logging.getLogger("AssignmentOperationIR")
ASSIGNEMENT_TYPE = Union["VALID_RVALUE", "VALID_LVALUE", Function, TupleVariable]


class Assignment(OperationWithLValue):
    def __init__(
        self,
        left_variable: "VALID_LVALUE",
        right_variable: Union["VALID_RVALUE", Function, TupleVariable],
        variable_return_type: "Type",
    ):
        assert is_valid_lvalue(left_variable)
        assert is_valid_rvalue(right_variable) or isinstance(
            right_variable, (Function, TupleVariable)
        )
        super(Assignment, self).__init__()
        self._variables: List["ASSIGNEMENT_TYPE"] = [left_variable, right_variable]
        self._lvalue: "VALID_LVALUE" = left_variable
        self._rvalue: Union["VALID_RVALUE", Function, TupleVariable] = right_variable
        self._variable_return_type: "Type" = variable_return_type

    @property
    def variables(self) -> List["ASSIGNEMENT_TYPE"]:
        return list(self._variables)

    @property
    def read(self) -> List[Union["VALID_RVALUE", Function, TupleVariable]]:
        return [self.rvalue]

    @property
    def variable_return_type(self) -> "Type":
        return self._variable_return_type

    @property
    def rvalue(self) -> Union["VALID_RVALUE", Function, TupleVariable]:
        return self._rvalue

    @property
    def lvalue(self) -> "VALID_LVALUE":
        return self._lvalue

    @lvalue.setter
    def lvalue(self, lvalue):
        self._lvalue = lvalue

    def __str__(self):
        lvalue = self.lvalue
        if isinstance(lvalue, IndexVariable):
            points = lvalue.points_to
            while isinstance(points, IndexVariable):
                points = points.points_to
            return "{} (->{}) := {}({})".format(self.lvalue, points, self.rvalue, self.rvalue.type)
        return "{}({}) := {}({})".format(
            self.lvalue, self.lvalue.type, self.rvalue, self.rvalue.type
        )
