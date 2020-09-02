from typing import Union, TYPE_CHECKING, Tuple
import math

from slither.core.solidity_types.type import Type
from slither.exceptions import SlitherException

if TYPE_CHECKING:
    from slither.core.declarations.structure import Structure
    from slither.core.declarations.enum import Enum
    from slither.core.declarations.contract import Contract

# pylint: disable=import-outside-toplevel
class UserDefinedType(Type):
    def __init__(self, t):
        from slither.core.declarations.structure import Structure
        from slither.core.declarations.enum import Enum
        from slither.core.declarations.contract import Contract

        assert isinstance(t, (Contract, Enum, Structure))
        super(UserDefinedType, self).__init__()
        self._type = t

    @property
    def type(self) -> Union["Contract", "Enum", "Structure"]:
        return self._type

    @property
    def storage_size(self) -> Tuple[int, bool]:
        from slither.core.declarations.structure import Structure
        from slither.core.declarations.enum import Enum
        from slither.core.declarations.contract import Contract

        if isinstance(self._type, Contract):
            return 20, False
        if isinstance(self._type, Enum):
            return int(math.ceil(math.log2(len(self._type.values)) / 8)), False
        if isinstance(self._type, Structure):
            # todo there's some duplicate logic here and slither_core, can we refactor this?
            slot = 0
            offset = 0
            for elem in self._type.elems_ordered:
                size, new_slot = elem.type.storage_size
                if new_slot:
                    if offset > 0:
                        slot += 1
                        offset = 0
                elif size + offset > 32:
                    slot += 1
                    offset = 0

                if new_slot:
                    slot += math.ceil(size / 32)
                else:
                    offset += size
            if offset > 0:
                slot += 1
            return slot * 32, True
        to_log = f"{self} does not have storage size"
        raise SlitherException(to_log)

    def __str__(self):
        from slither.core.declarations.structure import Structure
        from slither.core.declarations.enum import Enum

        if isinstance(self.type, (Enum, Structure)):
            return str(self.type.contract) + "." + str(self.type.name)
        return str(self.type.name)

    def __eq__(self, other):
        if not isinstance(other, UserDefinedType):
            return False
        return self.type == other.type

    def __hash__(self):
        return hash(str(self))
