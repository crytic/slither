from typing import TYPE_CHECKING

from slither.core.expressions.expression import Expression
from slither.core.expressions.expression_typed import ExpressionTyped

if TYPE_CHECKING:
    from slither.core.solidity_types.type import Type


class MemberAccess(ExpressionTyped):
    def __init__(self, member_name, member_type, expression):
        # assert isinstance(member_type, Type)
        # TODO member_type is not always a Type
        assert isinstance(expression, Expression)
        super(MemberAccess, self).__init__()
        self._type: "Type" = member_type
        self._member_name: str = member_name
        self._expression: Expression = expression

    @property
    def expression(self) -> Expression:
        return self._expression

    @property
    def member_name(self) -> str:
        return self._member_name

    @property
    def type(self) -> "Type":
        return self._type

    def __str__(self):
        return str(self.expression) + "." + self.member_name
