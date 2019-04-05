
from .variable_declaration import VariableDeclarationVyper
from slither.core.variables.event_variable import EventVariable

class EventVariableVyper(VariableDeclarationVyper, EventVariable):

    def _analyze_variable_attributes(self, arg_sig, indexed):
        """
        Analyze event variable attributes
        :param attributes: The event variable attributes to parse.
        :return: None
        """

        # Check for the indexed attribute
        self._indexed = indexed

        super()._analyze_variable_attributes(arg_sig)
