"""
Module detecting unused state variables
"""
from slither.core.compilation_unit import SlitherCompilationUnit
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.core.solidity_types import ArrayType
from slither.visitors.expression.export_values import ExportValues
from slither.core.variables.state_variable import StateVariable
from slither.formatters.variables.unused_state_variables import custom_format


def detect_unused(contract):
    if contract.is_signature_only():
        return None
    # Get all the variables read in all the functions and modifiers

    all_functions = contract.all_functions_called + contract.modifiers
    variables_used = [x.state_variables_read for x in all_functions]
    variables_used += [
        x.state_variables_written for x in all_functions if not x.is_constructor_variables
    ]

    array_candidates = [x.variables for x in all_functions]
    array_candidates = [i for sl in array_candidates for i in sl] + contract.state_variables
    array_candidates = [
        x.type.length for x in array_candidates if isinstance(x.type, ArrayType) and x.type.length
    ]
    array_candidates = [ExportValues(x).result() for x in array_candidates]
    array_candidates = [i for sl in array_candidates for i in sl]
    array_candidates = [v for v in array_candidates if isinstance(v, StateVariable)]

    # Flat list
    variables_used = [item for sublist in variables_used for item in sublist]
    variables_used = list(set(variables_used + array_candidates))

    # Return the variables unused that are not public
    return [x for x in contract.variables if x not in variables_used and x.visibility != "public"]


class UnusedStateVars(AbstractDetector):
    """
    Unused state variables detector
    """

    ARGUMENT = "unused-state"
    HELP = "Unused state variables"
    IMPACT = DetectorClassification.INFORMATIONAL
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#unused-state-variable"

    WIKI_TITLE = "Unused state variable"
    WIKI_DESCRIPTION = "Unused state variable."
    WIKI_EXPLOIT_SCENARIO = ""
    WIKI_RECOMMENDATION = "Remove unused state variables."

    def _detect(self):
        """Detect unused state variables"""
        results = []
        for c in self.compilation_unit.contracts_derived:
            unusedVars = detect_unused(c)
            if unusedVars:
                for var in unusedVars:
                    info = [var, " is never used in ", c, "\n"]
                    json = self.generate_result(info)
                    results.append(json)

        return results

    @staticmethod
    def _format(compilation_unit: SlitherCompilationUnit, result):
        custom_format(compilation_unit, result)
