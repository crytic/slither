from typing import List, Dict
from slither.utils.output import Output
from slither.core.compilation_unit import SlitherCompilationUnit
from slither.formatters.variables.unchanged_state_variables import custom_format
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from .unchanged_state_variables import UnchangedStateVariables


class CouldBeConstant(AbstractDetector):
    """
    State variables that could be declared as constant.
    Not all types for constants are implemented in Solidity as of 0.4.25.
    The only supported types are value types and strings (ElementaryType).
    Reference: https://solidity.readthedocs.io/en/latest/contracts.html#constant-state-variables
    """

    ARGUMENT = "constable-states"
    HELP = "State variables that could be declared constant"
    IMPACT = DetectorClassification.OPTIMIZATION
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#state-variables-that-could-be-declared-constant"

    WIKI_TITLE = "State variables that could be declared constant"
    WIKI_DESCRIPTION = "State variables that are not updated following deployment should be declared constant to save gas."
    WIKI_RECOMMENDATION = "Add the `constant` attribute to state variables that never change."

    def _detect(self) -> List[Output]:
        """Detect state variables that could be constant"""
        results = {}

        unchanged_state_variables = UnchangedStateVariables(self.compilation_unit)
        unchanged_state_variables.detect()

        for variable in unchanged_state_variables.constant_candidates:
            results[variable.canonical_name] = self.generate_result(
                [variable, " should be constant \n"]
            )

        # Order by canonical name for deterministic results
        return [results[k] for k in sorted(results)]

    @staticmethod
    def _format(compilation_unit: SlitherCompilationUnit, result: Dict) -> None:
        custom_format(compilation_unit, result, "constant")
