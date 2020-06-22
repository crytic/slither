from typing import TYPE_CHECKING

from slither.core.solidity_types.type import Type

if TYPE_CHECKING:
    from slither.core.declarations.contract import Contract


# Use to model the Type(X) function, which returns an undefined type
# https://solidity.readthedocs.io/en/latest/units-and-global-variables.html#type-information
class TypeInformation(Type):
    def __init__(self, c):
        from slither.core.declarations.contract import Contract

        assert isinstance(c, Contract)
        super(TypeInformation, self).__init__()
        self._type = c

    @property
    def type(self) -> "Contract":
        return self._type

    def __str__(self):
        return f"type({self.type.name})"

    def __eq__(self, other):
        if not isinstance(other, TypeInformation):
            return False
        return self.type == other.type
