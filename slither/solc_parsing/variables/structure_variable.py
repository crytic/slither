from typing import Dict

from .variable_declaration import VariableDeclarationSolc
from slither.core.variables.structure_variable import StructureVariable


class StructureVariableSolc(VariableDeclarationSolc):
    def __init__(self, variable: StructureVariable, variable_data: Dict):
        super(StructureVariableSolc, self).__init__(variable, variable_data)

    @property
    def underlying_variable(self) -> StructureVariable:
        # Todo: Not sure how to overcome this with mypy
        assert isinstance(self._variable, StructureVariable)
        return self._variable
