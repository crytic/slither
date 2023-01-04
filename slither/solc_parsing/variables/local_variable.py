from typing import Dict

from slither.solc_parsing.variables.variable_declaration import VariableDeclarationSolc
from slither.core.variables.local_variable import LocalVariable
from .variable_declaration import VariableDeclarationSolc
from ..types.types import VariableDeclarationStatement, VariableDeclaration

class LocalVariableSolc(VariableDeclarationSolc):
    def __init__(self, variable: LocalVariable, variable_data: VariableDeclarationStatement):
        super().__init__(variable, variable_data)

    @property
    def underlying_variable(self) -> LocalVariable:
        # Todo: Not sure how to overcome this with mypy
        assert isinstance(self._variable, LocalVariable)
        return self._variable

    def _analyze_variable_attributes(self, attributes: VariableDeclaration):
        self.underlying_variable.set_location(attributes.location)
        super()._analyze_variable_attributes(attributes)
