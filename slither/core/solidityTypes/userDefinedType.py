from slither.core.solidityTypes.type import Type

from slither.core.declarations.structure import Structure
from slither.core.declarations.enum import Enum
from slither.core.declarations.contract import Contract


class UserDefinedType(Type):

    def __init__(self, t):
        assert isinstance(t, (Contract, Enum, Structure))
        super(UserDefinedType, self).__init__()
        self._type = t

    @property
    def type(self):
        return self._type

    def __str__(self):
        if isinstance(self.type, (Enum, Structure)):
            return str(self.type.contract)+'.'+str(self.type.name)
        return str(self.type.name)

    def __eq__(self, other):
        if not isinstance(other, UserDefinedType):
            return False
        return self.type == other.type


    def __hash__(self):
        return hash(str(self))

