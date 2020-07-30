from slither.core.variables.state_variable import StateVariable
from .variable_declaration import VariableDeclarationSolc
from ..types.types import VariableDeclaration


class StateVariableSolc(VariableDeclarationSolc[StateVariable]):
    def __init__(self, variable: StateVariable, variable_data: VariableDeclaration):
        super().__init__(variable, variable_data)
