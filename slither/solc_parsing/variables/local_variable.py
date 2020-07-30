from slither.core.variables.local_variable import LocalVariable
from .variable_declaration import VariableDeclarationSolc
from ..types.types import VariableDeclarationStatement, VariableDeclaration


class LocalVariableSolc(VariableDeclarationSolc[LocalVariable]):
    def __init__(self, variable: LocalVariable, variable_data: VariableDeclarationStatement):
        super().__init__(variable, variable_data)

    def _analyze_variable_attributes(self, attributes: VariableDeclaration):
        self.underlying_variable.set_location(attributes.location)

        super()._analyze_variable_attributes(attributes)
