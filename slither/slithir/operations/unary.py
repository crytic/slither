import logging
from enum import Enum

from slither.slithir.operations.lvalue import OperationWithLValue
from slither.slithir.utils.utils import is_valid_lvalue, is_valid_rvalue
from slither.slithir.exceptions import SlithIRError

logger = logging.getLogger("BinaryOperationIR")


class UnaryType(Enum):
    BANG = 0  # !
    TILD = 1  # ~

    @staticmethod
    def get_type(operation_type, isprefix):
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
    def __init__(self, result, variable, operation_type):
        assert is_valid_rvalue(variable)
        assert is_valid_lvalue(result)
        super().__init__()
        self._variable = variable
        self._type = operation_type
        self._lvalue = result

    @property
    def read(self):
        return [self._variable]

    @property
    def rvalue(self):
        return self._variable

    @property
    def type(self):
        return self._type

    @property
    def type_str(self):
        return str(self._type)

    def __str__(self):
        return "{} = {} {} ".format(self.lvalue, self.type_str, self.rvalue)
