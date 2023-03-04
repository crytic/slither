"""
Gas: Detecting explicit initialization of variables with default values

"""
from collections import defaultdict

from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification

class DefaultVariableInitialization(AbstractDetector):
    """
    Gas: Detecting explicit initialization of variables with default values
    """

    ARGUMENT = "default-variable-initialization"
    HELP = "The variable can simply be declared instead of initialized to its default value"
    IMPACT = DetectorClassification.OPTIMIZATION
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = "https://github.com/demis1997/slither-gas-optimizer-detector/wiki/Solidity-Gas-Optimizations-and-Tricks#no-need-to-explicitly-initialize-variables-with-default-values"
    WIKI_TITLE = "No need to explicitly initialize variables with default values"
    WIKI_DESCRIPTION = "If a variable is not set/initialized, it is assumed to have the default value (0 for uint, false for bool, address(0) for address, etc.). Explicitly initializing it with its default value is an anti-pattern and wastes gas."

    def _get_variable_declarations(self):
        """
        Returns a list of all variable declarations in the contract.
        """
        variable_declarations = []
        for contract in self.contracts:
            for variable in contract.variables:
                variable_declarations.append(variable)
        return variable_declarations

    def analyze(self):
        """
        Analyzes the contract to detect explicit initialization of variables with default values.
        """
        variable_declarations = self._get_variable_declarations()
        for variable_declaration in variable_declarations:
            if variable_declaration.initial_value is not None and variable_declaration.initial_value.value == variable_declaration.typ.default_value:
                self.issue({
                    "variable_declaration": variable_declaration.name,
                    "line_number": variable_declaration.node.lineno,
                    "col_offset": variable_declaration.node.col_offset
                })
