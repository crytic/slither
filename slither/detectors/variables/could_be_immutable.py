from typing import List, Dict
from slither.utils.output import Output
from slither.core.compilation_unit import SlitherCompilationUnit
from slither.formatters.variables.unchanged_state_variables import custom_format
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from .unchanged_state_variables import UnchangedStateVariables


class CouldBeImmutable(AbstractDetector):
    """
    State variables that could be declared immutable.
    # Immutable attribute available in Solidity 0.6.5 and above
    # https://blog.soliditylang.org/2020/04/06/solidity-0.6.5-release-announcement/
    """

    # VULNERABLE_SOLC_VERSIONS =
    ARGUMENT = "immutable-states"
    HELP = "State variables that could be declared immutable"
    IMPACT = DetectorClassification.OPTIMIZATION
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#state-variables-that-could-be-declared-immutable"

    WIKI_TITLE = "State variables that could be declared immutable"
    WIKI_DESCRIPTION = "State variables that are not updated following deployment should be declared immutable to save gas."
    WIKI_RECOMMENDATION = "Add the `immutable` attribute to state variables that never change or are set only in the constructor."

    def _detect(self) -> List[Output]:
        """Detect state variables that could be immutable"""
        results = {}
        unchanged_state_variables = UnchangedStateVariables(self.compilation_unit)
        unchanged_state_variables.detect()

        for variable in unchanged_state_variables.immutable_candidates:
            results[variable.canonical_name] = self.generate_result(
                [variable, " should be immutable \n"]
            )

        # Order by canonical name for deterministic results
        return [results[k] for k in sorted(results)]

    @staticmethod
    def _format(compilation_unit: SlitherCompilationUnit, result: Dict) -> None:
        custom_format(compilation_unit, result, "immutable")
