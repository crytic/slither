from typing import TYPE_CHECKING, List

from slither.core.solidity_types.elementary_type import ElementaryType
from slither.slithir.operations.call import Call
from slither.slithir.operations.lvalue import OperationWithLValue
from slither.slithir.utils.utils import is_valid_lvalue

if TYPE_CHECKING:
    from slither.slithir.utils.utils import VALID_LVALUE, VALID_RVALUE


class NewElementaryType(Call, OperationWithLValue):
    def __init__(self, new_type: ElementaryType, lvalue: "VALID_LVALUE"):
        assert isinstance(new_type, ElementaryType)
        assert is_valid_lvalue(lvalue)
        super(NewElementaryType, self).__init__()
        self._type: ElementaryType = new_type
        self._lvalue: "VALID_LVALUE" = lvalue

    @property
    def type(self) -> ElementaryType:
        return self._type

    @property
    def read(self) -> List["VALID_RVALUE"]:
        return list(self.arguments)

    def __str__(self):
        args = [str(a) for a in self.arguments]

        return "{} = new {}({})".format(self.lvalue, self._type, ",".join(args))
