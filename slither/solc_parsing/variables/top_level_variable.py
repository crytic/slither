from typing import Dict

from slither.core.variables.top_level_variable import TopLevelVariable
from slither.solc_parsing.variables.variable_declaration import VariableDeclarationSolc


class TopLevelVariableSolc(VariableDeclarationSolc):
    def __init__(self, variable: TopLevelVariable, variable_data: Dict):
        super().__init__(variable, variable_data)

    @property
    def underlying_variable(self) -> TopLevelVariable:
        # Todo: Not sure how to overcome this with mypy
        assert isinstance(self._variable, TopLevelVariable)
        return self._variable
