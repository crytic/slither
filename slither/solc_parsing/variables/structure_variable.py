from typing import Dict

from slither.solc_parsing.variables.variable_declaration import VariableDeclarationSolc
from slither.core.variables.structure_variable import StructureVariable


class StructureVariableSolc(VariableDeclarationSolc[StructureVariable]):
    def __init__(self, variable: StructureVariable, variable_data: Dict):
        super().__init__(variable, variable_data)

    @property
    def underlying_variable(self) -> StructureVariable:
        return self._variable
