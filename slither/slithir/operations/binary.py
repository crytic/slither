import logging
from enum import Enum
from typing import List, Union

from slither.core.declarations import Function
from slither.core.solidity_types import ElementaryType
from slither.core.variables.variable import Variable
from slither.slithir.exceptions import SlithIRError
from slither.slithir.operations.lvalue import OperationWithLValue
from slither.slithir.utils.utils import is_valid_lvalue, is_valid_rvalue, LVALUE, RVALUE
from slither.slithir.variables import ReferenceVariable

logger = logging.getLogger("BinaryOperationIR")


class BinaryType(Enum):
    POWER = "**"
    MULTIPLICATION = "*"
    DIVISION = "/"
    MODULO = "%"
    ADDITION = "+"
    SUBTRACTION = "-"
    LEFT_SHIFT = "<<"
    RIGHT_SHIFT = ">>"
    AND = "&"
    CARET = "^"
    OR = "|"
    LESS = "<"
    GREATER = ">"
    LESS_EQUAL = "<="
    GREATER_EQUAL = ">="
    EQUAL = "=="
    NOT_EQUAL = "!="
    ANDAND = "&&"
    OROR = "||"

    @staticmethod
    def return_bool(operation_type: "BinaryType") -> bool:
        return operation_type in [
            BinaryType.OROR,
            BinaryType.ANDAND,
            BinaryType.LESS,
            BinaryType.GREATER,
            BinaryType.LESS_EQUAL,
            BinaryType.GREATER_EQUAL,
            BinaryType.EQUAL,
            BinaryType.NOT_EQUAL,
        ]

    @staticmethod
    def get_type(operation_type: str) -> "BinaryType":  # pylint: disable=too-many-branches
        if operation_type == "**":
            return BinaryType.POWER
        if operation_type == "*":
            return BinaryType.MULTIPLICATION
        if operation_type == "/":
            return BinaryType.DIVISION
        if operation_type == "%":
            return BinaryType.MODULO
        if operation_type == "+":
            return BinaryType.ADDITION
        if operation_type == "-":
            return BinaryType.SUBTRACTION
        if operation_type == "<<":
            return BinaryType.LEFT_SHIFT
        if operation_type == ">>":
            return BinaryType.RIGHT_SHIFT
        if operation_type == "&":
            return BinaryType.AND
        if operation_type == "^":
            return BinaryType.CARET
        if operation_type == "|":
            return BinaryType.OR
        if operation_type == "<":
            return BinaryType.LESS
        if operation_type == ">":
            return BinaryType.GREATER
        if operation_type == "<=":
            return BinaryType.LESS_EQUAL
        if operation_type == ">=":
            return BinaryType.GREATER_EQUAL
        if operation_type == "==":
            return BinaryType.EQUAL
        if operation_type == "!=":
            return BinaryType.NOT_EQUAL
        if operation_type == "&&":
            return BinaryType.ANDAND
        if operation_type == "||":
            return BinaryType.OROR

        raise SlithIRError(f"get_type: Unknown operation type {operation_type})")

    def can_be_checked_for_overflow(self) -> bool:
        return self in [
            BinaryType.POWER,
            BinaryType.MULTIPLICATION,
            BinaryType.ADDITION,
            BinaryType.SUBTRACTION,
            BinaryType.DIVISION,
        ]


class Binary(OperationWithLValue):
    def __init__(
        self,
        result: Variable,
        left_variable: Union[RVALUE, Function],
        right_variable: Union[RVALUE, Function],
        operation_type: BinaryType,
    ) -> None:
        assert is_valid_rvalue(left_variable) or isinstance(left_variable, Function)
        assert is_valid_rvalue(right_variable) or isinstance(right_variable, Function)
        assert is_valid_lvalue(result)
        assert isinstance(operation_type, BinaryType)
        super().__init__()
        self._variables = [left_variable, right_variable]
        self._type = operation_type
        self._lvalue = result
        if BinaryType.return_bool(operation_type):
            result.set_type(ElementaryType("bool"))
        else:
            result.set_type(left_variable.type)

    @property
    def read(self) -> List[Union[RVALUE, LVALUE, Function]]:
        return [self.variable_left, self.variable_right]

    @property
    def get_variable(self) -> List[Union[RVALUE, Function]]:
        return self._variables

    @property
    def variable_left(self) -> Union[RVALUE, Function]:
        return self._variables[0]  # type: ignore

    @property
    def variable_right(self) -> Union[RVALUE, Function]:
        return self._variables[1]  # type: ignore

    @property
    def type(self) -> BinaryType:
        return self._type

    @property
    def type_str(self) -> str:
        if self.node.scope.is_checked and self._type.can_be_checked_for_overflow():
            return "(c)" + str(self._type.value)
        return str(self._type.value)

    def __str__(self) -> str:
        lvalue = self.lvalue
        assert lvalue
        if isinstance(lvalue, ReferenceVariable):
            points = lvalue.points_to
            while isinstance(points, ReferenceVariable):
                points = points.points_to
            return f"{str(lvalue)}(-> {points}) = {self.variable_left} {self.type_str} {self.variable_right}"

        return f"{str(lvalue)}({lvalue.type}) = {self.variable_left} {self.type_str} {self.variable_right}"
