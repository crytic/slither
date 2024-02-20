from typing import List, Union

from slither.core.declarations import Contract
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.core.solidity_types.type_alias import TypeAlias
from slither.core.solidity_types.user_defined_type import UserDefinedType
from slither.core.solidity_types.array_type import ArrayType
from slither.core.source_mapping.source_mapping import SourceMapping
from slither.slithir.operations.lvalue import OperationWithLValue
from slither.slithir.utils.utils import is_valid_lvalue, is_valid_rvalue
from slither.slithir.variables.temporary import TemporaryVariable
from slither.slithir.variables.temporary_ssa import TemporaryVariableSSA


class TypeConversion(OperationWithLValue):
    def __init__(
        self,
        result: Union[TemporaryVariableSSA, TemporaryVariable],
        variable: SourceMapping,
        variable_type: Union[TypeAlias, UserDefinedType, ElementaryType],
    ) -> None:
        super().__init__()
        assert is_valid_rvalue(variable) or isinstance(variable, Contract)
        assert is_valid_lvalue(result)
        assert isinstance(variable_type, (TypeAlias, UserDefinedType, ElementaryType, ArrayType))

        self._variable = variable
        self._type: Union[TypeAlias, UserDefinedType, ElementaryType, ArrayType] = variable_type
        self._lvalue = result

    @property
    def variable(self) -> SourceMapping:
        return self._variable

    @property
    def type(
        self,
    ) -> Union[TypeAlias, UserDefinedType, ElementaryType,]:
        return self._type

    @property
    def read(self) -> List[SourceMapping]:
        return [self.variable]

    def __str__(self) -> str:
        return str(self.lvalue) + f" = CONVERT {self.variable} to {self.type}"
