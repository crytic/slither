from slither.core.variables.local_variable_init_from_tuple import LocalVariableInitFromTuple
from .variable_declaration import VariableDeclarationSolc
from ..types.types import VariableDeclarationStatement


class LocalVariableInitFromTupleSolc(VariableDeclarationSolc[LocalVariableInitFromTuple]):
    def __init__(self, variable: LocalVariableInitFromTuple, variable_data: VariableDeclarationStatement, index: int):
        super().__init__(variable, variable_data)
        variable.tuple_index = index
