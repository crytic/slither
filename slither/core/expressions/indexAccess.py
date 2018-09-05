from slither.core.expressions.expressionTyped import ExpressionTyped
from slither.core.solidityTypes.type import Type


class IndexAccess(ExpressionTyped):

    def __init__(self, left_expression, right_expression, index_type):
        super(IndexAccess, self).__init__()
        self._expressions = [left_expression, right_expression]
        # TODO type of undexAccess is not always a Type
#        assert isinstance(index_type, Type)
        self._type = index_type

    @property
    def expressions(self):
        return self._expressions

    @property
    def expression_left(self):
        return self._expressions[0]

    @property
    def expression_right(self):
        return self._expressions[1]

    @property
    def type(self):
        return self._type

    def __str__(self):
        return str(self.expression_left) + '[' + str(self.expression_right) + ']'

