
from .variable_declaration import VariableDeclarationVyper
from slither.core.variables.local_variable import LocalVariable

class LocalVariableVyper(VariableDeclarationVyper, LocalVariable):
    pass
