from slither.core.expressions.expression import Expression
from slither.core.expressions.expression_typed import ExpressionTyped


class MemberAccess(ExpressionTyped):

    def __init__(self, member_name, member_type, expression):
        # assert isinstance(member_type, Type)
        # TODO member_type is not always a Type
        assert isinstance(expression, Expression)
        super(MemberAccess, self).__init__()
        self._type = member_type
        self._member_name = member_name
        self._expression = expression

    @property
    def expression(self):
        return self._expression

    @property
    def member_name(self):
        return self._member_name

    @property
    def type(self):
        return self._type

    def __str__(self):
        return str(self.expression) + '.' + self.member_name
