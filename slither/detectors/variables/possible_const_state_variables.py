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
from slither.core.expressions import CallExpression, NewContract


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
    HELP = "State variables that could be declared constant or immutable"
    IMPACT = DetectorClassification.OPTIMIZATION
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#state-variables-that-could-be-declared-constant-or-immutable"

    WIKI_TITLE = "State variables that could be declared constant or immutable"
    WIKI_DESCRIPTION = "State variables that are not updated following deployment should be declared constant or immutable to save gas."
    WIKI_RECOMMENDATION = (
        "Add the `constant` or `immutable` attribute to state variables that never change."
    )

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

        # B b = new B(); b cannot be constant, so filter out and recommend it be immutable
        if isinstance(v.expression, CallExpression) and isinstance(
            v.expression.called, NewContract
        ):
            return False

        export = ExportValues(v.expression)
        values = export.result()
        if not values:
            return True
        else:
            return all(
                (val in self.valid_solidity_function or _is_constant_var(val) for val in values)
            )

    def _detect(self) -> List[Output]:
        """Detect state variables that could be constant or immutable"""
        results = {}

        variables = []
        functions = []
        for c in self.compilation_unit.contracts:
            variables.append(c.state_variables)
            functions.append(c.all_functions_called)

        valid_candidates: Set[StateVariable] = {
            item for sublist in variables for item in sublist if _valid_candidate(item)
        }

        all_functions: List[Function] = list(
            {item1 for sublist in functions for item1 in sublist if isinstance(item1, Function)}
        )

        variables_written = []
        constructor_variables_written = []
        for f in all_functions:
            if f.is_constructor_variables:
                constructor_variables_written.append(f.state_variables_written)
            else:
                variables_written.append(f.state_variables_written)

        variables_written = {item for sublist in variables_written for item in sublist}
        constructor_variables_written = {
            item for sublist in constructor_variables_written for item in sublist
        }
        for v in valid_candidates:
            if v not in variables_written:
                if self._constant_initial_expression(v):
                    results[v.canonical_name] = self.generate_result([v, " should be constant \n"])

                # immutable attribute available in Solidity 0.6.5 and above
                # https://blog.soliditylang.org/2020/04/06/solidity-0.6.5-release-announcement/
                elif (
                    v in constructor_variables_written
                    and self.compilation_unit.solc_version > "0.6.4"
                ):
                    results[v.canonical_name] = self.generate_result([v, " should be immutable \n"])

        # Order by canonical name for deterministic results
        return [results[k] for k in sorted(results)]

    @staticmethod
    def _format(compilation_unit: SlitherCompilationUnit, result: Dict) -> None:
        custom_format(compilation_unit, result)
