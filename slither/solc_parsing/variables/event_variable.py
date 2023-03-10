from typing import Dict

from slither.solc_parsing.variables.variable_declaration import VariableDeclarationSolc
from slither.core.variables.event_variable import EventVariable


class EventVariableSolc(VariableDeclarationSolc):
    def __init__(self, variable: EventVariable, variable_data: Dict):
        super().__init__(variable, variable_data)

    @property
    def underlying_variable(self) -> EventVariable:
        # Todo: Not sure how to overcome this with mypy
        assert isinstance(self._variable, EventVariable)
        return self._variable

    def _analyze_variable_attributes(self, attributes: Dict) -> None:
        """
        Analyze event variable attributes
        :param attributes: The event variable attributes to parse.
        :return: None
        """

        # Check for the indexed attribute
        if "indexed" in attributes:
            self.underlying_variable.indexed = attributes["indexed"]

        super()._analyze_variable_attributes(attributes)
