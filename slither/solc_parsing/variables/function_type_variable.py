from typing import Dict

from slither.solc_parsing.variables.variable_declaration import VariableDeclarationSolc
from slither.core.variables.function_type_variable import FunctionTypeVariable


class FunctionTypeVariableSolc(VariableDeclarationSolc[FunctionTypeVariable]):
    def __init__(self, variable: FunctionTypeVariable, variable_data: Dict):
        super().__init__(variable, variable_data)

    @property
    def underlying_variable(self) -> FunctionTypeVariable:
        return self._variable
