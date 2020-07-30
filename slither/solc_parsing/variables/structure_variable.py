from slither.solc_parsing.variables.variable_declaration import VariableDeclarationSolc
from slither.core.variables.structure_variable import StructureVariable
from ..types.types import VariableDeclaration


class StructureVariableSolc(VariableDeclarationSolc[StructureVariable]):
    def __init__(self, variable: StructureVariable, variable_data: VariableDeclaration):
        super().__init__(variable, variable_data)
