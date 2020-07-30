from slither.solc_parsing.types.types import VariableDeclaration
from slither.solc_parsing.variables.variable_declaration import VariableDeclarationSolc
from slither.core.variables.function_type_variable import FunctionTypeVariable


class FunctionTypeVariableSolc(VariableDeclarationSolc[FunctionTypeVariable]):
    def __init__(self, variable: FunctionTypeVariable, variable_data: VariableDeclaration):
        super().__init__(variable, variable_data)
