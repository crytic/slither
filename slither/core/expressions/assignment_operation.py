import logging
from enum import Enum
from typing import Optional, TYPE_CHECKING, List

from slither.core.expressions.expression_typed import ExpressionTyped
from slither.core.expressions.expression import Expression
from slither.core.exceptions import SlitherCoreError

if TYPE_CHECKING:
    from slither.core.solidity_types.type import Type

logger = logging.getLogger("AssignmentOperation")


class AssignmentOperationType(Enum):
    ASSIGN = 0  # =
    ASSIGN_OR = 1  # |=
    ASSIGN_CARET = 2  # ^=
    ASSIGN_AND = 3  # &=
    ASSIGN_LEFT_SHIFT = 4  # <<=
    ASSIGN_RIGHT_SHIFT = 5  # >>=
    ASSIGN_ADDITION = 6  # +=
    ASSIGN_SUBTRACTION = 7  # -=
    ASSIGN_MULTIPLICATION = 8  # *=
    ASSIGN_DIVISION = 9  # /=
    ASSIGN_MODULO = 10  # %=

    @staticmethod
    def get_type(operation_type: "AssignmentOperationType"):
        if operation_type == "=":
            return AssignmentOperationType.ASSIGN
        if operation_type == "|=":
            return AssignmentOperationType.ASSIGN_OR
        if operation_type == "^=":
            return AssignmentOperationType.ASSIGN_CARET
        if operation_type == "&=":
            return AssignmentOperationType.ASSIGN_AND
        if operation_type == "<<=":
            return AssignmentOperationType.ASSIGN_LEFT_SHIFT
        if operation_type == ">>=":
            return AssignmentOperationType.ASSIGN_RIGHT_SHIFT
        if operation_type == "+=":
            return AssignmentOperationType.ASSIGN_ADDITION
        if operation_type == "-=":
            return AssignmentOperationType.ASSIGN_SUBTRACTION
        if operation_type == "*=":
            return AssignmentOperationType.ASSIGN_MULTIPLICATION
        if operation_type == "/=":
            return AssignmentOperationType.ASSIGN_DIVISION
        if operation_type == "%=":
            return AssignmentOperationType.ASSIGN_MODULO

        raise SlitherCoreError("get_type: Unknown operation type {})".format(operation_type))

    def __str__(self):
        if self == AssignmentOperationType.ASSIGN:
            return "="
        if self == AssignmentOperationType.ASSIGN_OR:
            return "|="
        if self == AssignmentOperationType.ASSIGN_CARET:
            return "^="
        if self == AssignmentOperationType.ASSIGN_AND:
            return "&="
        if self == AssignmentOperationType.ASSIGN_LEFT_SHIFT:
            return "<<="
        if self == AssignmentOperationType.ASSIGN_RIGHT_SHIFT:
            return ">>="
        if self == AssignmentOperationType.ASSIGN_ADDITION:
            return "+="
        if self == AssignmentOperationType.ASSIGN_SUBTRACTION:
            return "-="
        if self == AssignmentOperationType.ASSIGN_MULTIPLICATION:
            return "*="
        if self == AssignmentOperationType.ASSIGN_DIVISION:
            return "/="
        if self == AssignmentOperationType.ASSIGN_MODULO:
            return "%="
        raise SlitherCoreError("str: Unknown operation type {})".format(self))


class AssignmentOperation(ExpressionTyped):
    def __init__(
        self,
        left_expression: Expression,
        right_expression: Expression,
        expression_type: AssignmentOperationType,
        expression_return_type: Optional["Type"],
    ):
        assert isinstance(left_expression, Expression)
        assert isinstance(right_expression, Expression)
        super().__init__()
        left_expression.set_lvalue()
        self._expressions = [left_expression, right_expression]
        self._type = expression_type
        self._expression_return_type: Optional["Type"] = expression_return_type

    @property
    def expressions(self) -> List[Expression]:
        return self._expressions

    @property
    def expression_return_type(self) -> Optional["Type"]:
        return self._expression_return_type

    @property
    def expression_left(self) -> Expression:
        return self._expressions[0]

    @property
    def expression_right(self) -> Expression:
        return self._expressions[1]

    @property
    def type(self) -> AssignmentOperationType:
        return self._type

    def __str__(self):
        return str(self.expression_left) + " " + str(self.type) + " " + str(self.expression_right)
