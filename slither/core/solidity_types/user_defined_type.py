from typing import Union, TYPE_CHECKING, Tuple, Any
import math

from slither.core.solidity_types.type import Type
from slither.exceptions import SlitherException

if TYPE_CHECKING:
    from slither.core.declarations.structure import Structure
    from slither.core.declarations.enum import Enum
    from slither.core.declarations.contract import Contract

# pylint: disable=import-outside-toplevel
class UserDefinedType(Type):
    def __init__(self, t: Union["Enum", "Contract", "Structure"]) -> None:
        from slither.core.declarations.structure import Structure
        from slither.core.declarations.enum import Enum
        from slither.core.declarations.contract import Contract

        assert isinstance(t, (Contract, Enum, Structure))
        super().__init__()
        self._type = t

    @property
    def is_dynamic(self) -> bool:
        return False

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

    def __str__(self) -> str:
        from slither.core.declarations.structure_contract import StructureContract
        from slither.core.declarations.enum_contract import EnumContract

        type_used = self.type
        if isinstance(type_used, (EnumContract, StructureContract)):
            return str(type_used.contract) + "." + str(type_used.name)
        return str(type_used.name)

    def __eq__(self, other: Any) -> bool:
        from slither.core.declarations.contract import Contract

        if not isinstance(other, UserDefinedType):
            return False
        if isinstance(self.type, Contract) and isinstance(other.type, Contract):
            return self.type == other.type.name
        return self.type == other.type

    def __hash__(self) -> int:
        return hash(str(self))
