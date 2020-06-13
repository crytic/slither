from typing import List, TYPE_CHECKING

from slither.slithir.operations.lvalue import OperationWithLValue

from slither.slithir.utils.utils import is_valid_lvalue, is_valid_rvalue

if TYPE_CHECKING:
    from slither.slithir.utils.utils import VALID_RVALUE, VALID_LVALUE


class Delete(OperationWithLValue):
    """
        Delete has a lvalue, as it has for effect to change the value
        of its operand
    """

    def __init__(self, lvalue: "VALID_LVALUE", variable: "VALID_RVALUE"):
        assert is_valid_lvalue(variable)
        assert is_valid_rvalue(variable)
        super(Delete, self).__init__()
        self._variable: "VALID_RVALUE" = variable
        self._lvalue: "VALID_LVALUE" = lvalue

    @property
    def read(self) -> List["VALID_RVALUE"]:
        return [self.variable]

    @property
    def variable(self) -> "VALID_RVALUE":
        return self._variable

    def __str__(self):
        return "{} = delete {} ".format(self.lvalue, self.variable)
