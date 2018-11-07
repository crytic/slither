from slither.core.expressions.expression import Expression
from slither.core.solidity_types.elementary_type import ElementaryType

class NewElementaryType(Expression):

    def __init__(self, new_type):
        assert isinstance(new_type, ElementaryType)
        super(NewElementaryType, self).__init__()
        self._type = new_type

    @property
    def type(self):
        return self._type

    def __str__(self):
        return 'new ' + str(self._type)

