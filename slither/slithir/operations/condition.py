from typing import List, Union
from slither.slithir.operations.operation import Operation

from slither.slithir.utils.utils import is_valid_rvalue
from slither.core.variables.local_variable import LocalVariable
from slither.slithir.variables.constant import Constant
from slither.slithir.variables.local_variable import LocalIRVariable
from slither.slithir.variables.temporary import TemporaryVariable
from slither.slithir.variables.temporary_ssa import TemporaryVariableSSA
from slither.core.variables.variable import Variable


class Condition(Operation):
    """
    Condition
    Only present as last operation in conditional node
    """

    def __init__(
        self,
        value: Union[
            LocalVariable, TemporaryVariableSSA, TemporaryVariable, Constant, LocalIRVariable
        ],
    ) -> None:
        assert is_valid_rvalue(value)
        super().__init__()
        self._value = value

    @property
    def read(
        self,
    ) -> List[
        Union[LocalIRVariable, Constant, LocalVariable, TemporaryVariableSSA, TemporaryVariable]
    ]:
        return [self.value]

    @property
    def value(self) -> Variable:
        return self._value

    def __str__(self):
        return f"CONDITION {self.value}"
