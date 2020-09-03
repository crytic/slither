import logging
from enum import Enum
from typing import List

from slither.core.expressions.expression_typed import ExpressionTyped
from slither.core.expressions.expression import Expression
from slither.core.exceptions import SlitherCoreError


logger = logging.getLogger("BinaryOperation")


class BinaryOperationType(Enum):
    POWER = 0  # **
    MULTIPLICATION = 1  # *
    DIVISION = 2  # /
    MODULO = 3  # %
    ADDITION = 4  # +
    SUBTRACTION = 5  # -
    LEFT_SHIFT = 6  # <<
    RIGHT_SHIFT = 7  # >>>
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

    # YUL specific operators
    # TODO: investigate if we can remove these
    # Find the types earlier on, and do the conversion
    DIVISION_SIGNED = 19
    MODULO_SIGNED = 20
    LESS_SIGNED = 21
    GREATER_SIGNED = 22
    RIGHT_SHIFT_ARITHMETIC = 23

    @staticmethod
    def get_type(operation_type: "BinaryOperation"):  # pylint: disable=too-many-branches
        if operation_type == "**":
            return BinaryOperationType.POWER
        if operation_type == "*":
            return BinaryOperationType.MULTIPLICATION
        if operation_type == "/":
            return BinaryOperationType.DIVISION
        if operation_type == "%":
            return BinaryOperationType.MODULO
        if operation_type == "+":
            return BinaryOperationType.ADDITION
        if operation_type == "-":
            return BinaryOperationType.SUBTRACTION
        if operation_type == "<<":
            return BinaryOperationType.LEFT_SHIFT
        if operation_type == ">>":
            return BinaryOperationType.RIGHT_SHIFT
        if operation_type == "&":
            return BinaryOperationType.AND
        if operation_type == "^":
            return BinaryOperationType.CARET
        if operation_type == "|":
            return BinaryOperationType.OR
        if operation_type == "<":
            return BinaryOperationType.LESS
        if operation_type == ">":
            return BinaryOperationType.GREATER
        if operation_type == "<=":
            return BinaryOperationType.LESS_EQUAL
        if operation_type == ">=":
            return BinaryOperationType.GREATER_EQUAL
        if operation_type == "==":
            return BinaryOperationType.EQUAL
        if operation_type == "!=":
            return BinaryOperationType.NOT_EQUAL
        if operation_type == "&&":
            return BinaryOperationType.ANDAND
        if operation_type == "||":
            return BinaryOperationType.OROR
        if operation_type == "/'":
            return BinaryOperationType.DIVISION_SIGNED
        if operation_type == "%'":
            return BinaryOperationType.MODULO_SIGNED
        if operation_type == "<'":
            return BinaryOperationType.LESS_SIGNED
        if operation_type == ">'":
            return BinaryOperationType.GREATER_SIGNED
        if operation_type == ">>'":
            return BinaryOperationType.RIGHT_SHIFT_ARITHMETIC

        raise SlitherCoreError(
            "get_type: Unknown operation type {})".format(operation_type)
        )

    def __str__(self):  # pylint: disable=too-many-branches
        if self == BinaryOperationType.POWER:
            return "**"
        if self == BinaryOperationType.MULTIPLICATION:
            return "*"
        if self == BinaryOperationType.DIVISION:
            return "/"
        if self == BinaryOperationType.MODULO:
            return "%"
        if self == BinaryOperationType.ADDITION:
            return "+"
        if self == BinaryOperationType.SUBTRACTION:
            return "-"
        if self == BinaryOperationType.LEFT_SHIFT:
            return "<<"
        if self == BinaryOperationType.RIGHT_SHIFT:
            return ">>"
        if self == BinaryOperationType.AND:
            return "&"
        if self == BinaryOperationType.CARET:
            return "^"
        if self == BinaryOperationType.OR:
            return "|"
        if self == BinaryOperationType.LESS:
            return "<"
        if self == BinaryOperationType.GREATER:
            return ">"
        if self == BinaryOperationType.LESS_EQUAL:
            return "<="
        if self == BinaryOperationType.GREATER_EQUAL:
            return ">="
        if self == BinaryOperationType.EQUAL:
            return "=="
        if self == BinaryOperationType.NOT_EQUAL:
            return "!="
        if self == BinaryOperationType.ANDAND:
            return "&&"
        if self == BinaryOperationType.OROR:
            return "||"
        if self == BinaryOperationType.DIVISION_SIGNED:
            return "/'"
        if self == BinaryOperationType.MODULO_SIGNED:
            return "%'"
        if self == BinaryOperationType.LESS_SIGNED:
            return "<'"
        if self == BinaryOperationType.GREATER_SIGNED:
            return ">'"
        if self == BinaryOperationType.RIGHT_SHIFT_ARITHMETIC:
            return ">>'"
        raise SlitherCoreError("str: Unknown operation type {})".format(self))


class BinaryOperation(ExpressionTyped):
    def __init__(self, left_expression, right_expression, expression_type):
        assert isinstance(left_expression, Expression)
        assert isinstance(right_expression, Expression)
        super().__init__()
        self._expressions = [left_expression, right_expression]
        self._type: BinaryOperationType = expression_type

    @property
    def expressions(self) -> List[Expression]:
        return self._expressions

    @property
    def expression_left(self) -> Expression:
        return self._expressions[0]

    @property
    def expression_right(self) -> Expression:
        return self._expressions[1]

    @property
    def type(self) -> BinaryOperationType:
        return self._type

    def __str__(self):
        return (
            str(self.expression_left)
            + " "
            + str(self.type)
            + " "
            + str(self.expression_right)
        )
