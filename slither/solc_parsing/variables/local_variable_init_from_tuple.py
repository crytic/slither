
from .variable_declaration import VariableDeclarationSolc
from slither.core.variables.local_variable_init_from_tuple import LocalVariableInitFromTuple

class LocalVariableInitFromTupleSolc(VariableDeclarationSolc, LocalVariableInitFromTuple):

    def __init__(self, var, index):
        super(LocalVariableInitFromTupleSolc, self).__init__(var)
        self._tuple_index = index

