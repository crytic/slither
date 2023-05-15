import logging
from typing import List, Union

from slither.core.declarations.function import Function
from slither.core.solidity_types import Type
from slither.slithir.operations.lvalue import OperationWithLValue
from slither.slithir.utils.utils import is_valid_lvalue, is_valid_rvalue, RVALUE, LVALUE
from slither.slithir.variables import TupleVariable, ReferenceVariable

logger = logging.getLogger("AssignmentOperationIR")


class Assignment(OperationWithLValue):
    def __init__(
        self,
        left_variable: LVALUE,
        right_variable: Union[RVALUE, Function, TupleVariable],
        variable_return_type: Type,
    ) -> None:
        assert is_valid_lvalue(left_variable)
        assert is_valid_rvalue(right_variable) or isinstance(
            right_variable, (Function, TupleVariable)
        )
        super().__init__()
        self._variables = [left_variable, right_variable]
        self._lvalue: LVALUE = left_variable
        self._rvalue: Union[RVALUE, Function, TupleVariable] = right_variable
        self._variable_return_type = variable_return_type

    @property
    def variables(self) -> List[Union[LVALUE, RVALUE, Function, TupleVariable]]:
        return list(self._variables)

    @property
    def read(self) -> List[Union[RVALUE, Function, TupleVariable]]:
        return [self.rvalue]

    @property
    def variable_return_type(self) -> Type:
        return self._variable_return_type

    @property
    def rvalue(self) -> Union[RVALUE, Function, TupleVariable]:
        return self._rvalue

    def __str__(self) -> str:
        lvalue = self.lvalue
        assert lvalue
        if lvalue and isinstance(lvalue, ReferenceVariable):
            points = lvalue.points_to
            while isinstance(points, ReferenceVariable):
                points = points.points_to
            return f"{lvalue}({lvalue.type}) (->{points}) := {self.rvalue}({self.rvalue.type})"
        return f"{lvalue}({lvalue.type}) := {self.rvalue}({self.rvalue.type})"
