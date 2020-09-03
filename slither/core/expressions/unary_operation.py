import logging
from enum import Enum

from slither.core.expressions.expression_typed import ExpressionTyped
from slither.core.expressions.expression import Expression
from slither.core.exceptions import SlitherCoreError

logger = logging.getLogger("UnaryOperation")


class UnaryOperationType(Enum):
    BANG = 0  # !
    TILD = 1  # ~
    DELETE = 2  # delete
    PLUSPLUS_PRE = 3  # ++
    MINUSMINUS_PRE = 4  # --
    PLUSPLUS_POST = 5  # ++
    MINUSMINUS_POST = 6  # --
    PLUS_PRE = 7  # for stuff like uint(+1)
    MINUS_PRE = 8  # for stuff like uint(-1)

    @staticmethod
    def get_type(operation_type, isprefix):
        if isprefix:
            if operation_type == "!":
                return UnaryOperationType.BANG
            if operation_type == "~":
                return UnaryOperationType.TILD
            if operation_type == "delete":
                return UnaryOperationType.DELETE
            if operation_type == "++":
                return UnaryOperationType.PLUSPLUS_PRE
            if operation_type == "--":
                return UnaryOperationType.MINUSMINUS_PRE
            if operation_type == "+":
                return UnaryOperationType.PLUS_PRE
            if operation_type == "-":
                return UnaryOperationType.MINUS_PRE
        else:
            if operation_type == "++":
                return UnaryOperationType.PLUSPLUS_POST
            if operation_type == "--":
                return UnaryOperationType.MINUSMINUS_POST
        raise SlitherCoreError(
            "get_type: Unknown operation type {}".format(operation_type)
        )

    def __str__(self):
        if self == UnaryOperationType.BANG:
            return "!"
        if self == UnaryOperationType.TILD:
            return "~"
        if self == UnaryOperationType.DELETE:
            return "delete"
        if self == UnaryOperationType.PLUS_PRE:
            return "+"
        if self == UnaryOperationType.MINUS_PRE:
            return "-"
        if self in [UnaryOperationType.PLUSPLUS_PRE, UnaryOperationType.PLUSPLUS_POST]:
            return "++"
        if self in [
            UnaryOperationType.MINUSMINUS_PRE,
            UnaryOperationType.MINUSMINUS_POST,
        ]:
            return "--"

        raise SlitherCoreError("str: Unknown operation type {}".format(self))

    @staticmethod
    def is_prefix(operation_type):
        if operation_type in [
            UnaryOperationType.BANG,
            UnaryOperationType.TILD,
            UnaryOperationType.DELETE,
            UnaryOperationType.PLUSPLUS_PRE,
            UnaryOperationType.MINUSMINUS_PRE,
            UnaryOperationType.PLUS_PRE,
            UnaryOperationType.MINUS_PRE,
        ]:
            return True
        if operation_type in [
            UnaryOperationType.PLUSPLUS_POST,
            UnaryOperationType.MINUSMINUS_POST,
        ]:
            return False

        raise SlitherCoreError(
            "is_prefix: Unknown operation type {}".format(operation_type)
        )


class UnaryOperation(ExpressionTyped):
    def __init__(self, expression, expression_type):
        assert isinstance(expression, Expression)
        super().__init__()
        self._expression: Expression = expression
        self._type: UnaryOperationType = expression_type
        if expression_type in [
            UnaryOperationType.DELETE,
            UnaryOperationType.PLUSPLUS_PRE,
            UnaryOperationType.MINUSMINUS_PRE,
            UnaryOperationType.PLUSPLUS_POST,
            UnaryOperationType.MINUSMINUS_POST,
            UnaryOperationType.PLUS_PRE,
            UnaryOperationType.MINUS_PRE,
        ]:
            expression.set_lvalue()

    @property
    def expression(self) -> Expression:
        return self._expression

    @property
    def type(self) -> UnaryOperationType:
        return self._type

    @property
    def is_prefix(self) -> bool:
        return UnaryOperationType.is_prefix(self._type)

    def __str__(self):
        if self.is_prefix:
            return str(self.type) + " " + str(self._expression)
        return str(self._expression) + " " + str(self.type)
