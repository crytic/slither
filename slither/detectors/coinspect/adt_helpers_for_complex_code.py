from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.core.declarations import Function
from slither.utils.output import Output
from slither.utils.code_complexity import compute_cyclomatic_complexity

class CoinspectHelperFunctionsDetector(AbstractDetector):
    """
    Detector to check if helper functions are used to improve readability of complex operations
    """

    ARGUMENT = "helper-functions-usage"
    HELP = "Check if helper functions are used for complex operations"
    IMPACT = DetectorClassification.INFORMATIONAL
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#magic-numbers"
    WIKI_TITLE = "Helper Functions for Complex Code"
    WIKI_DESCRIPTION = "Identifies if helper functions are used to break down complex code."
    WIKI_EXPLOIT_SCENARIO = "Complex function can lead to errors and reduce code readability."
    WIKI_RECOMMENDATION = "Break down complex functions into internal and simple helper methods."

    def _is_complex_function(self, function: Function) -> bool:
        print(function, compute_cyclomatic_complexity(function))
        if compute_cyclomatic_complexity(function) > 7:
            return True
        return False

    def _is_potential_helper_function(self, function: Function) -> bool:
        # Check if the function is private or internal
        if function.visibility not in ["private", "internal"]:
            return False
        
        # Check if the function is relatively small (less than 15 nodes)
        if len(function.nodes) >= 15:
            return False
        
        # Check if the function doesn't make external calls
        if(len(function.high_level_calls) != 0):
            return False
       
        return True

    def _detect(self):
        results = []

        for contract in self.compilation_unit.contracts_derived:
            complex_functions = [f for f in contract.functions if self._is_complex_function(f)]
            print(complex_functions)
            potential_helpers = [f for f in contract.functions if self._is_potential_helper_function(f)]

            for complex_func in complex_functions:
                helpers_used = [h for h in potential_helpers if h in complex_func.internal_calls]
                
                if not helpers_used:
                    info = [
                        "Complex function ",
                        complex_func,
                        " does not use any helper functions.\n"
                    ]
                    res = self.generate_result(info)
                    results.append(res)
                else:
                    # Optionally, you can report on complex functions that do use helpers
                    info = [
                        "Complex function ",
                        complex_func,
                        f" uses {len(helpers_used)} helper function(s).\n"
                    ]
                    res = self.generate_result(info)
                    results.append(res)

        return results