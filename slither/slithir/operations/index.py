from typing import List, Union
from slither.core.declarations import SolidityVariableComposed
from slither.slithir.operations.lvalue import OperationWithLValue
from slither.slithir.utils.utils import is_valid_lvalue, is_valid_rvalue
from slither.slithir.variables.reference import ReferenceVariable
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.core.source_mapping.source_mapping import SourceMapping
from slither.core.variables.variable import Variable
from slither.slithir.variables.reference_ssa import ReferenceVariableSSA


class Index(OperationWithLValue):
    def __init__(
        self,
        result: Union[ReferenceVariable, ReferenceVariableSSA],
        left_variable: Variable,
        right_variable: SourceMapping,
        index_type: Union[ElementaryType, str],
    ) -> None:
        super().__init__()
        assert is_valid_lvalue(left_variable) or left_variable == SolidityVariableComposed(
            "msg.data"
        )
        assert is_valid_rvalue(right_variable)
        assert isinstance(result, ReferenceVariable)
        self._variables = [left_variable, right_variable]
        self._type = index_type
        self._lvalue = result

    @property
    def read(self) -> List[SourceMapping]:
        return list(self.variables)

    @property
    def variables(self) -> List[SourceMapping]:
        return self._variables

    @property
    def variable_left(self) -> Variable:
        return self._variables[0]

    @property
    def variable_right(self) -> SourceMapping:
        return self._variables[1]

    @property
    def index_type(self) -> Union[ElementaryType, str]:
        return self._type

    def __str__(self):
        return f"{self.lvalue}({self.lvalue.type}) -> {self.variable_left}[{self.variable_right}]"
