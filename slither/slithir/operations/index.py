from typing import List, Union

from slither.core.declarations import SolidityVariableComposed
from slither.core.source_mapping.source_mapping import SourceMapping
from slither.core.variables.variable import Variable
from slither.core.variables.top_level_variable import TopLevelVariable
from slither.slithir.operations.lvalue import OperationWithLValue
from slither.slithir.utils.utils import is_valid_lvalue, is_valid_rvalue, RVALUE, LVALUE
from slither.slithir.variables.reference import ReferenceVariable


class Index(OperationWithLValue):
    def __init__(
        self, result: ReferenceVariable, left_variable: Variable, right_variable: RVALUE
    ) -> None:
        super().__init__()
        assert (
            is_valid_lvalue(left_variable)
            or left_variable == SolidityVariableComposed("msg.data")
            or isinstance(left_variable, TopLevelVariable)
        )
        assert is_valid_rvalue(right_variable)
        assert isinstance(result, ReferenceVariable)
        self._variables = [left_variable, right_variable]
        self._lvalue: ReferenceVariable = result

    @property
    def read(self) -> List[SourceMapping]:
        return list(self.variables)

    @property
    def variables(self) -> List[Union[LVALUE, RVALUE, SolidityVariableComposed]]:
        return self._variables  # type: ignore

    @property
    def variable_left(self) -> Union[LVALUE, SolidityVariableComposed]:
        return self._variables[0]  # type: ignore

    @property
    def variable_right(self) -> RVALUE:
        return self._variables[1]  # type: ignore

    def __str__(self) -> str:
        return f"{self.lvalue}({self.lvalue.type}) -> {self.variable_left}[{self.variable_right}]"
