from typing import Dict

from slither.solc_parsing.variables.variable_declaration import VariableDeclarationSolc
from slither.core.variables.local_variable_init_from_tuple import LocalVariableInitFromTuple


class LocalVariableInitFromTupleSolc(VariableDeclarationSolc[LocalVariableInitFromTuple]):
    def __init__(self, variable: LocalVariableInitFromTuple, variable_data: Dict, index: int):
        super().__init__(variable, variable_data)
        variable.tuple_index = index

    @property
    def underlying_variable(self) -> LocalVariableInitFromTuple:
        return self._variable
