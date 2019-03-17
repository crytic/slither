
from .variable_declaration import VariableDeclarationVyper
from slither.core.variables.state_variable import StateVariable

class StateVariableVyper(VariableDeclarationVyper, StateVariable): pass
