from typing import TYPE_CHECKING, List, Optional

from slither.slithir.operations.call import Call
from slither.slithir.operations.lvalue import OperationWithLValue

from slither.slithir.utils.utils import is_valid_lvalue

from slither.core.declarations.structure import Structure


if TYPE_CHECKING:
    from slither.slithir.utils.utils import VALID_LVALUE, VALID_RVALUE


class NewStructure(Call, OperationWithLValue):
    def __init__(self, structure: Structure, lvalue: Optional["VALID_LVALUE"]):
        super(NewStructure, self).__init__()
        assert isinstance(structure, Structure)
        assert is_valid_lvalue(lvalue)
        self._structure: Structure = structure
        # todo create analyze to add the contract instance
        self._lvalue: Optional["VALID_LVALUE"] = lvalue

    @property
    def read(self) -> List["VALID_RVALUE"]:
        return self._unroll(self.arguments)

    @property
    def structure(self) -> Structure:
        return self._structure

    @property
    def structure_name(self) -> str:
        return self.structure.name

    def __str__(self):
        args = [str(a) for a in self.arguments]
        return "{} = new {}({})".format(self.lvalue, self.structure_name, ",".join(args))
