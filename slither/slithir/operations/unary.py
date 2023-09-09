import logging
from typing import List, Union
from enum import Enum

from slither.slithir.operations.lvalue import OperationWithLValue
from slither.slithir.utils.utils import is_valid_lvalue, is_valid_rvalue
from slither.slithir.exceptions import SlithIRError
from slither.core.variables.local_variable import LocalVariable
from slither.slithir.variables.constant import Constant
from slither.slithir.variables.local_variable import LocalIRVariable
from slither.slithir.variables.temporary import TemporaryVariable
from slither.slithir.variables.temporary_ssa import TemporaryVariableSSA


logger = logging.getLogger("BinaryOperationIR")


class UnaryType(Enum):
    BANG = "!"
    TILD = "~"

    @staticmethod
    def get_type(operation_type, isprefix):
        if isprefix:
            if operation_type == "!":
                return UnaryType.BANG
            if operation_type == "~":
                return UnaryType.TILD
        raise SlithIRError(f"get_type: Unknown operation type {operation_type}")


class Unary(OperationWithLValue):
    def __init__(
        self,
        result: Union[TemporaryVariableSSA, TemporaryVariable],
        variable: Union[Constant, LocalIRVariable, LocalVariable],
        operation_type: UnaryType,
    ) -> None:
        assert is_valid_rvalue(variable)
        assert is_valid_lvalue(result)
        super().__init__()
        self._variable = variable
        self._type = operation_type
        self._lvalue = result

    @property
    def read(self) -> List[Union[Constant, LocalIRVariable, LocalVariable]]:
        return [self._variable]

    @property
    def rvalue(self) -> Union[Constant, LocalVariable]:
        return self._variable

    @property
    def type(self) -> UnaryType:
        return self._type

    @property
    def type_str(self):
        return str(self._type)

    def __str__(self):
        return f"{self.lvalue} = {self.type_str} {self.rvalue} "
