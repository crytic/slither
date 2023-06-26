"""
Module detecting state variables that could be declared as constant
"""
from typing import Set, List
from packaging import version
from slither.core.compilation_unit import SlitherCompilationUnit
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.core.solidity_types.user_defined_type import UserDefinedType
from slither.core.variables.variable import Variable

from slither.visitors.expression.export_values import ExportValues
from slither.core.declarations import Contract, Function
from slither.core.declarations.solidity_variables import SolidityFunction
from slither.core.variables.state_variable import StateVariable
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


def _constant_initial_expression(v: Variable) -> bool:
    if not v.expression:
        return True

    # B b = new B(); b cannot be constant, so filter out and recommend it be immutable
    if isinstance(v.expression, CallExpression) and isinstance(v.expression.called, NewContract):
        return False

    export = ExportValues(v.expression)
    values = export.result()
    if not values:
        return True

    return all((val in valid_solidity_function or _is_constant_var(val) for val in values))


class UnchangedStateVariables:
    """
    Find state variables that could be declared as constant or immutable (not written after deployment).
    """

    def __init__(self, compilation_unit: SlitherCompilationUnit) -> None:
        self.compilation_unit = compilation_unit
        self._constant_candidates: List[StateVariable] = []
        self._immutable_candidates: List[StateVariable] = []

    @property
    def immutable_candidates(self) -> List[StateVariable]:
        """Return the immutable candidates"""
        return self._immutable_candidates

    @property
    def constant_candidates(self) -> List[StateVariable]:
        """Return the constant candidates"""
        return self._constant_candidates

    def detect(self) -> None:
        """Detect state variables that could be constant or immutable"""
        for c in self.compilation_unit.contracts_derived:
            if c.is_signature_only():
                continue
            variables = []
            functions = []

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
            variables_initialized = []
            for f in all_functions:
                if f.is_constructor_variables:
                    variables_initialized.extend(f.state_variables_written)
                elif f.is_constructor:
                    constructor_variables_written.extend(f.state_variables_written)
                else:
                    variables_written.extend(f.state_variables_written)

            for v in valid_candidates:
                if v not in variables_written:
                    if _constant_initial_expression(v) and v not in constructor_variables_written:
                        self.constant_candidates.append(v)

                    elif (
                        not v.type.is_dynamic
                        and version.parse(self.compilation_unit.solc_version)
                        >= version.parse("0.6.5")
                        and (v in constructor_variables_written or v in variables_initialized)
                    ):
                        self.immutable_candidates.append(v)
