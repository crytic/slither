import logging
from enum import Enum
from typing import TYPE_CHECKING, List

from slither.core.solidity_types import ElementaryType
from slither.slithir.exceptions import SlithIRError
from slither.slithir.operations.lvalue import OperationWithLValue
from slither.slithir.utils.utils import is_valid_lvalue, is_valid_rvalue
from slither.slithir.variables import IndexVariable

if TYPE_CHECKING:
    from slither.slithir.utils.utils import VALID_RVALUE, VALID_LVALUE

logger = logging.getLogger("BinaryOperationIR")


class BinaryType(Enum):
    POWER = 0  # **
    MULTIPLICATION = 1  # *
    DIVISION = 2  # /
    MODULO = 3  # %
    ADDITION = 4  # +
    SUBTRACTION = 5  # -
    LEFT_SHIFT = 6  # <<
    RIGHT_SHIFT = 7  # >>
    AND = 8  # &
    CARET = 9  # ^
    OR = 10  # |
    LESS = 11  # <
    GREATER = 12  # >
    LESS_EQUAL = 13  # <=
    GREATER_EQUAL = 14  # >=
    EQUAL = 15  # ==
    NOT_EQUAL = 16  # !=
    ANDAND = 17  # &&
    OROR = 18  # ||

    @staticmethod
    def return_bool(operation_type):
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
    def get_type(operation_type):
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

        raise SlithIRError("get_type: Unknown operation type {})".format(operation_type))

    def __str__(self):
        if self == BinaryType.POWER:
            return "**"
        if self == BinaryType.MULTIPLICATION:
            return "*"
        if self == BinaryType.DIVISION:
            return "/"
        if self == BinaryType.MODULO:
            return "%"
        if self == BinaryType.ADDITION:
            return "+"
        if self == BinaryType.SUBTRACTION:
            return "-"
        if self == BinaryType.LEFT_SHIFT:
            return "<<"
        if self == BinaryType.RIGHT_SHIFT:
            return ">>"
        if self == BinaryType.AND:
            return "&"
        if self == BinaryType.CARET:
            return "^"
        if self == BinaryType.OR:
            return "|"
        if self == BinaryType.LESS:
            return "<"
        if self == BinaryType.GREATER:
            return ">"
        if self == BinaryType.LESS_EQUAL:
            return "<="
        if self == BinaryType.GREATER_EQUAL:
            return ">="
        if self == BinaryType.EQUAL:
            return "=="
        if self == BinaryType.NOT_EQUAL:
            return "!="
        if self == BinaryType.ANDAND:
            return "&&"
        if self == BinaryType.OROR:
            return "||"
        raise SlithIRError("str: Unknown operation type {} {})".format(self, type(self)))


class Binary(OperationWithLValue):
    def __init__(
        self,
        result: "VALID_LVALUE",
        left_variable: "VALID_RVALUE",
        right_variable: "VALID_RVALUE",
        operation_type: BinaryType,
    ):
        assert is_valid_rvalue(left_variable)
        assert is_valid_rvalue(right_variable)
        assert is_valid_lvalue(result)
        assert isinstance(operation_type, BinaryType)
        super(Binary, self).__init__()
        self._variables: List["VALID_RVALUE"] = [left_variable, right_variable]
        self._type: BinaryType = operation_type
        self._lvalue: "VALID_LVALUE" = result
        if BinaryType.return_bool(operation_type):
            result.set_type(ElementaryType("bool"))
        else:
            result.set_type(left_variable.type)

    @property
    def read(self) -> List["VALID_RVALUE"]:
        return [self.variable_left, self.variable_right]

    @property
    def get_variable(self) -> List["VALID_RVALUE"]:
        return self._variables

    @property
    def variable_left(self) -> "VALID_RVALUE":
        return self._variables[0]

    @property
    def variable_right(self) -> "VALID_RVALUE":
        return self._variables[1]

    @property
    def type(self) -> BinaryType:
        return self._type

    @property
    def lvalue(self) -> "VALID_LVALUE":
        return self._lvalue

    @lvalue.setter
    def lvalue(self, lvalue):
        self._lvalue = lvalue

    def __str__(self):
        if isinstance(self.lvalue, IndexVariable):
            points = self.lvalue.points_to
            while isinstance(points, IndexVariable):
                points = points.points_to
            return "{}(-> {}) = {} {} {}".format(
                str(self.lvalue), points, self.variable_left, str(self.type), self.variable_right
            )
        return "{}({}) = {} {} {}".format(
            str(self.lvalue),
            self.lvalue.type,
            self.variable_left,
            str(self.type),
            self.variable_right,
        )
