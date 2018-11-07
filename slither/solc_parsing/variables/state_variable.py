
from .variable_declaration import VariableDeclarationSolc
from slither.core.variables.state_variable import StateVariable

class StateVariableSolc(VariableDeclarationSolc, StateVariable): pass
