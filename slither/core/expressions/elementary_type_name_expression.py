"""
    This expression does nothing, if a contract used it, its probably a bug
"""
from slither.core.expressions.expression import Expression
from slither.core.solidity_types.type import Type

class ElementaryTypeNameExpression(Expression):

    def __init__(self, t):
        assert isinstance(t, Type)
        super(ElementaryTypeNameExpression, self).__init__()
        self._type = t

    @property
    def type(self):
        return self._type

    def __str__(self):
        return str(self._type)

