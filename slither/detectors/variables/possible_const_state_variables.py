"""
Module detecting state variables that could be declared as constant
"""
from typing import Set, List, Dict

from slither.core.compilation_unit import SlitherCompilationUnit
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.core.solidity_types.user_defined_type import UserDefinedType
from slither.core.variables.variable import Variable
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.utils.output import Output
from slither.visitors.expression.export_values import ExportValues
from slither.core.declarations import Contract, Function
from slither.core.declarations.solidity_variables import SolidityFunction
from slither.core.variables.state_variable import StateVariable
from slither.formatters.variables.possible_const_state_variables import custom_format


def _is_valid_type(v: StateVariable) -> bool:
    t = v.type
    if isinstance(t, ElementaryType):
        return True
    if isinstance(t, UserDefinedType) and isinstance(t.type, Contract):
        return True
    return False


def _valid_candidate(v: StateVariable) -> bool:
    return _is_valid_type(v) and not (v.is_constant or v.is_immutable)


def _is_constant_var(v: Variable) -> bool:
    if isinstance(v, StateVariable):
        return v.is_constant
    return False


class ConstCandidateStateVars(AbstractDetector):
    """
    State variables that could be declared as constant detector.
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
    WIKI_DESCRIPTION = "Constant state variables should be declared constant to save gas."
    WIKI_RECOMMENDATION = "Add the `constant` attributes to state variables that never change."

    # https://solidity.readthedocs.io/en/v0.5.2/contracts.html#constant-state-variables
    valid_solidity_function = [
        SolidityFunction("keccak256()"),
        SolidityFunction("keccak256(bytes)"),
        SolidityFunction("sha256()"),
        SolidityFunction("sha256(bytes)"),
        SolidityFunction("ripemd160()"),
        SolidityFunction("ripemd160(bytes)"),
        SolidityFunction("ecrecover(bytes32,uint8,bytes32,bytes32)"),
        SolidityFunction("addmod(uint256,uint256,uint256)"),
        SolidityFunction("mulmod(uint256,uint256,uint256)"),
    ]

    def _constant_initial_expression(self, v: Variable) -> bool:
        if not v.expression:
            return True

        export = ExportValues(v.expression)
        values = export.result()
        if not values:
            return True
        if all((val in self.valid_solidity_function or _is_constant_var(val) for val in values)):
            return True
        return False

    def _detect(self) -> List[Output]:
        """Detect state variables that could be const"""
        results = []

        all_variables_l = [c.state_variables for c in self.compilation_unit.contracts]
        all_variables: Set[StateVariable] = {
            item for sublist in all_variables_l for item in sublist
        }
        all_non_constant_elementary_variables = {v for v in all_variables if _valid_candidate(v)}

        all_functions_nested = [c.all_functions_called for c in self.compilation_unit.contracts]
        all_functions = list(
            {
                item1
                for sublist in all_functions_nested
                for item1 in sublist
                if isinstance(item1, Function)
            }
        )

        all_variables_written = [
            f.state_variables_written for f in all_functions if not f.is_constructor_variables
        ]
        all_variables_written = {item for sublist in all_variables_written for item in sublist}

        constable_variables: List[Variable] = [
            v
            for v in all_non_constant_elementary_variables
            if (v not in all_variables_written) and self._constant_initial_expression(v)
        ]
        # Order for deterministic results
        constable_variables = sorted(constable_variables, key=lambda x: x.canonical_name)

        # Create a result for each finding
        for v in constable_variables:
            info = [v, " should be constant\n"]
            json = self.generate_result(info)
            results.append(json)

        return results

    @staticmethod
    def _format(compilation_unit: SlitherCompilationUnit, result: Dict) -> None:
        custom_format(compilation_unit, result)
