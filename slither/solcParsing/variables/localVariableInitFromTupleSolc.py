
from .variableDeclarationSolc import VariableDeclarationSolc
from slither.core.variables.localVariableInitFromTuple import LocalVariableInitFromTuple

class LocalVariableInitFromTupleSolc(VariableDeclarationSolc, LocalVariableInitFromTuple):

    def __init__(self, var, index):
        super(LocalVariableInitFromTupleSolc, self).__init__(var)
        self._tuple_index = index

