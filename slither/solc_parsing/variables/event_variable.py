from typing import Dict

from slither.solc_parsing.variables.variable_declaration import VariableDeclarationSolc
from slither.core.variables.event_variable import EventVariable
from slither.solc_parsing.types.types import VariableDeclaration

class EventVariableSolc(VariableDeclarationSolc[EventVariable]):
    def __init__(self, variable: EventVariable, variable_data: VariableDeclaration):
        super().__init__(variable, variable_data)

    @property
    def underlying_variable(self) -> EventVariable:
        return self._variable

    def _analyze_variable_attributes(self, attributes: VariableDeclaration):
        """
        Analyze event variable attributes
        :param attributes: The event variable attributes to parse.
        :return: None
        """

        if attributes.indexed:
            self.underlying_variable.indexed = attributes.indexed

        super()._analyze_variable_attributes(attributes)
