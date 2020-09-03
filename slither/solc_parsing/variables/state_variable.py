from typing import Dict

from slither.solc_parsing.variables.variable_declaration import VariableDeclarationSolc
from slither.core.variables.state_variable import StateVariable


class StateVariableSolc(VariableDeclarationSolc):
    def __init__(self, variable: StateVariable, variable_data: Dict):
        super().__init__(variable, variable_data)

    @property
    def underlying_variable(self) -> StateVariable:
        # Todo: Not sure how to overcome this with mypy
        assert isinstance(self._variable, StateVariable)
        return self._variable
