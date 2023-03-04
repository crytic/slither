from collections import defaultdict
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification, Issue
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.solc_parsing.variables.state_variable import StateVariable

class GasModifierCheck(AbstractDetector):
    """
    Gas: Using a modifier instead of a function will save gas.
    """

    ARGUMENT = "modifier-check"
    HELP = "Rather than writing a function, you could trade that out for a modifier that does the same thing."
    IMPACT = DetectorClassification.OPTIMIZATION
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = "https://github.com/demis1997/slither-gas-optimizer-detector/wiki/Solidity-Gas-Optimizations-and-Tricks#use-modifiers-instead-of-functions-to-save-gas"
    WIKI_TITLE = "Use Modifiers Instead of Functions To Save Gas"
    WIKI_DESCRIPTION = "It is more efficient gas-wise to deploy with a modifier where applicable rather than with a function." 

    def _evaluate(self):
        function_calls = self.contract.get_all_function_calls()
        for function_call in function_calls:
            if function_call.is_state_modifying() and not function_call.called_from_modifier():
                function_decl = function_call.function_definition
                # check if the function can be refactored as a modifier
                if len(function_decl.modifiers) == 0 and len(function_decl.parameters) == 0 and not isinstance(function_decl.return_type, StateVariable):
                    self._issues.append(Issue(function_decl, 'Consider using a modifier instead of a function to save gas.', self, confidence=DetectorClassification.HIGH))
