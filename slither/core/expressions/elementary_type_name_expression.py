"""
    This expression does nothing, if a contract used it, its probably a bug
"""
from slither.core.expressions.expression import Expression
from slither.core.solidity_types.type import Type
from slither.core.solidity_types.elementary_type import ElementaryType


class ElementaryTypeNameExpression(Expression):
    def __init__(self, t: ElementaryType) -> None:
        assert isinstance(t, Type)
        super().__init__()
        self._type = t

    @property
    def type(self) -> Type:
        return self._type

    @type.setter
    def type(self, new_type: Type):
        assert isinstance(new_type, Type)
        self._type = new_type

    def __str__(self) -> str:
        return str(self._type)
