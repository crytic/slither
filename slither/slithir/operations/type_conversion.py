from typing import List, Union
from slither.core.declarations import Contract
from slither.core.solidity_types.type import Type
from slither.slithir.operations.lvalue import OperationWithLValue
from slither.slithir.utils.utils import is_valid_lvalue, is_valid_rvalue
import slither.core.declarations.contract
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.core.solidity_types.type_alias import TypeAliasContract, TypeAliasTopLevel
from slither.core.solidity_types.user_defined_type import UserDefinedType
from slither.core.source_mapping.source_mapping import SourceMapping
from slither.slithir.variables.temporary import TemporaryVariable
from slither.slithir.variables.temporary_ssa import TemporaryVariableSSA


class TypeConversion(OperationWithLValue):
    def __init__(
        self,
        result: Union[TemporaryVariableSSA, TemporaryVariable],
        variable: SourceMapping,
        variable_type: Union[TypeAliasContract, UserDefinedType, ElementaryType, TypeAliasTopLevel],
    ) -> None:
        super().__init__()
        assert is_valid_rvalue(variable) or isinstance(variable, Contract)
        assert is_valid_lvalue(result)
        assert isinstance(variable_type, Type)

        self._variable = variable
        self._type = variable_type
        self._lvalue = result

    @property
    def variable(self) -> SourceMapping:
        return self._variable

    @property
    def type(
        self,
    ) -> Union[
        TypeAliasContract,
        TypeAliasTopLevel,
        slither.core.declarations.contract.Contract,
        UserDefinedType,
        ElementaryType,
    ]:
        return self._type

    @property
    def read(self) -> List[SourceMapping]:
        return [self.variable]

    def __str__(self):
        return str(self.lvalue) + f" = CONVERT {self.variable} to {self.type}"
