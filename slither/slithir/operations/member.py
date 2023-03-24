from typing import List, Union
from slither.core.declarations import Contract, Function
from slither.core.declarations.custom_error import CustomError
from slither.core.declarations.enum import Enum
from slither.core.declarations.solidity_import_placeholder import SolidityImportPlaceHolder
from slither.core.solidity_types import ElementaryType
from slither.slithir.operations.lvalue import OperationWithLValue
from slither.slithir.utils.utils import is_valid_rvalue, RVALUE
from slither.slithir.variables.constant import Constant
from slither.slithir.variables.reference import ReferenceVariable
from slither.core.source_mapping.source_mapping import SourceMapping
from slither.slithir.variables.reference_ssa import ReferenceVariableSSA


class Member(OperationWithLValue):
    def __init__(
        self,
        variable_left: SourceMapping,
        variable_right: Constant,
        result: Union[ReferenceVariable, ReferenceVariableSSA],
    ) -> None:
        # Function can happen for something like
        # library FunctionExtensions {
        #     function h(function() internal _t, uint8) internal {  }
        # }
        # contract FunctionMembers {
        #     using FunctionExtensions for function();
        #
        #     function f() public {
        #         f.h(1);
        #     }
        # }
        # Can be an ElementaryType because of bytes.concat, string.concat
        assert is_valid_rvalue(variable_left) or isinstance(
            variable_left,
            (Contract, Enum, Function, CustomError, SolidityImportPlaceHolder, ElementaryType),
        )

        assert isinstance(variable_right, Constant)
        assert isinstance(result, ReferenceVariable)
        super().__init__()
        self._variable_left: Union[
            RVALUE, Contract, Enum, Function, CustomError, SolidityImportPlaceHolder, ElementaryType
        ] = variable_left
        self._variable_right = variable_right
        self._lvalue = result
        self._gas = None
        self._value = None

    @property
    def read(self) -> List[SourceMapping]:
        return [self.variable_left, self.variable_right]

    @property
    def variable_left(
        self,
    ) -> Union[
        RVALUE, Contract, Enum, Function, CustomError, SolidityImportPlaceHolder, ElementaryType
    ]:
        return self._variable_left

    @property
    def variable_right(self) -> Constant:
        return self._variable_right

    @property
    def call_value(self):
        return self._value

    @call_value.setter
    def call_value(self, v):
        self._value = v

    @property
    def call_gas(self):
        return self._gas

    @call_gas.setter
    def call_gas(self, gas):
        self._gas = gas

    def __str__(self):
        return f"{self.lvalue}({self.lvalue.type}) -> {self.variable_left}.{self.variable_right}"
