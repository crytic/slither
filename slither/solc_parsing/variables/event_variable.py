
from .variable_declaration import VariableDeclarationSolc
from slither.core.variables.event_variable import EventVariable

class EventVariableSolc(VariableDeclarationSolc, EventVariable): pass
