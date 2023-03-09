from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
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

    def _detect(self):
        detected_functions = []
        function_calls = self.contract.get_all_function_calls()
        for function_call in function_calls:
            if function_call.is_state_modifying() and not function_call.called_from_modifier():
                function_decl = function_call.function_definition
                # check if the function can be refactored as a modifier
                if len(function_decl.modifiers) == 0 and len(function_decl.parameters) == 0 and not isinstance(function_decl.return_type, StateVariable):
                    detected_functions.append(function_decl)
        
        issues = {}
        for function_decl in detected_functions:
            description = f"Consider using a modifier instead of a function '{function_decl.name}' to save gas."
            issues[function_decl.node_id] = {
                "title": "Gas Optimization - Consider using a modifier instead of a function",
                "description": description,
                "type": self.__class__.__name__,
                "address": self.contract.address,
                "metadata": {
                    "function_name": function_decl.name,
                },
                "severity": DetectorClassification.HIGH,
                "confidence": DetectorClassification.MEDIUM,
                "gas_saved": None,
            }
        
        return issues
