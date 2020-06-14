import logging
from enum import Enum
from typing import List, TYPE_CHECKING

from slither.slithir.operations.lvalue import OperationWithLValue
from slither.slithir.utils.utils import is_valid_lvalue, is_valid_rvalue
from slither.slithir.exceptions import SlithIRError

if TYPE_CHECKING:
    from slither.slithir.utils.utils import VALID_RVALUE, VALID_LVALUE

logger = logging.getLogger("BinaryOperationIR")


class UnaryType(Enum):
    BANG = 0  # !
    TILD = 1  # ~

    @staticmethod
    def get_type(operation_type: str, isprefix: bool) -> "UnaryType":
        if isprefix:
            if operation_type == "!":
                return UnaryType.BANG
            if operation_type == "~":
                return UnaryType.TILD
        raise SlithIRError("get_type: Unknown operation type {}".format(operation_type))

    def __str__(self):
        if self == UnaryType.BANG:
            return "!"
        if self == UnaryType.TILD:
            return "~"

        raise SlithIRError("str: Unknown operation type {}".format(self))


class Unary(OperationWithLValue):
    def __init__(self, result: "VALID_LVALUE", variable: "VALID_RVALUE", operation_type: UnaryType):
        assert is_valid_rvalue(variable)
        assert is_valid_lvalue(result)
        super(Unary, self).__init__()
        self._variable = variable
        self._type = operation_type
        self._lvalue = result

    @property
    def read(self) -> List["VALID_RVALUE"]:
        return [self._variable]

    @property
    def rvalue(self) -> "VALID_RVALUE":
        return self._variable

    @property
    def type(self) -> UnaryType:
        return self._type

    @property
    def lvalue(self) -> "VALID_LVALUE":
        return self._lvalue

    @lvalue.setter
    def lvalue(self, lvalue):
        self._lvalue = lvalue

    def __str__(self):
        return "{} = {} {} ".format(self.lvalue, self.type, self.rvalue)
