"""
Module detecting state variables that could be declared as immutable
"""
from slither.core.compilation_unit import SlitherCompilationUnit
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.formatters.variables.possible_const_state_variables import custom_format


class ImmutableCandidateStateVars(AbstractDetector):
    """
    State variables that could be declared as immutable detector.
    Only value types can be declared as immutable
    Reference: https://docs.soliditylang.org/en/latest/contracts.html#immutable
    """

    ARGUMENT = "immutable-states"
    HELP = "State variables that could be declared immutable"
    IMPACT = DetectorClassification.OPTIMIZATION
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation"

    WIKI_TITLE = "State variables that could be declared immutable"
    WIKI_DESCRIPTION = "State variables should be declared immutable whenever possible to save gas."
    WIKI_RECOMMENDATION = "Add the `immutable` attributes to state variables that never change after assigned once."

    @staticmethod
    def _valid_candidate(v):
        return isinstance(v.type, ElementaryType) and not (v.is_constant or v.is_immutable)

    @staticmethod
    def _can_be_immutable(v):
        return str(v.type) != "string" and str(v.type) != "bytes"

    def _detect(self):
        """Detect state variables that could be declared immutable"""
        results = []

        all_variables = [c.state_variables for c in self.compilation_unit.contracts]
        all_variables = {item for sublist in all_variables for item in sublist}
        all_candidates = {
            v for v in all_variables if self._valid_candidate(v)
        }

        all_functions = [c.all_functions_called for c in self.compilation_unit.contracts]
        all_functions = list({item for sublist in all_functions for item in sublist})

        all_variables_written = [
            f.state_variables_written for f in all_functions if not f.is_constructor and not f.is_constructor_variables
        ]
        all_variables_written = {item for sublist in all_variables_written for item in sublist}

        immutable_variables = [
            v
            for v in all_candidates
            if (not v in all_variables_written)
        ]
        # Order for deterministic results
        immutable_variables = sorted(immutable_variables, key=lambda x: x.canonical_name)

        # Create a result for each finding
        for v in immutable_variables:
            info = [v, " can be declared immutable\n"]
            json = self.generate_result(info)
            results.append(json)

        return results

    @staticmethod
    def _format(compilation_unit: SlitherCompilationUnit, result):
        custom_format(compilation_unit, result)