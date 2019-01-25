
from .variable_declaration import VariableDeclarationSolc
from slither.core.variables.event_variable import EventVariable

class EventVariableSolc(VariableDeclarationSolc, EventVariable):

    def _analyze_variable_attributes(self, attributes):
        """
        Analyze event variable attributes
        :param attributes: The event variable attributes to parse.
        :return: None
        """

        # Check for the indexed attribute
        if 'indexed' in attributes:
            self._indexed = attributes['indexed']

        super(EventVariableSolc, self)._analyze_variable_attributes(attributes)

