"""
Module detecting state variables that could be declared as constant
"""

from packaging import version
from slither.core.compilation_unit import SlitherCompilationUnit
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.core.solidity_types.user_defined_type import UserDefinedType
from slither.core.variables.variable import Variable

from slither.visitors.expression.export_values import ExportValues
from slither.core.declarations import Contract, Function
from slither.core.declarations.solidity_variables import SolidityFunction
from slither.core.variables.local_variable import LocalVariable
from slither.core.variables.state_variable import StateVariable
from slither.core.expressions import CallExpression, NewContract
from slither.slithir.operations import InternalCall, LibraryCall
from slither.slithir.variables import LocalIRVariable, StateIRVariable


def _is_valid_type(v: StateVariable) -> bool:
    t = v.type
    if isinstance(t, ElementaryType):
        return True
    if isinstance(t, UserDefinedType) and isinstance(t.type, Contract):
        return True
    return False


def _valid_candidate(v: StateVariable) -> bool:
    return _is_valid_type(v)


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

    return all(val in valid_solidity_function or _is_constant_var(val) for val in values)


def _storage_param_calls(function: Function):
    """
    Yield (callee, argument, parameter) for each argument passed to a storage parameter
    of an internal or library call in function
    """
    for ir in function.slithir_ssa_operations:
        if isinstance(ir, (InternalCall, LibraryCall)) and isinstance(ir.function, Function):
            for arg, param in zip(ir.arguments, ir.function.parameters, strict=False):
                if param.is_storage:
                    yield ir.function, arg, param


def _may_write_storage_param(
    function: Function, param: LocalVariable, explored: set[tuple[Function, LocalVariable]]
) -> bool:
    """
    Return true if function may write to the storage pointed to by its parameter param:
    - param is written in function (including through `x.slot := param.slot` in assembly), or
    - param is forwarded to a storage parameter of a call that may write it, or that returns a
      storage reference (e.g. OpenZeppelin StorageSlot.getStringSlot)

    view/pure functions cannot write storage, so a read-only use is not considered a write
    """
    if (function, param) in explored:
        return False
    explored.add((function, param))

    if function.view or function.pure:
        return False

    if param in function.variables_written:
        return True

    for callee, arg, callee_param in _storage_param_calls(function):
        if isinstance(arg, LocalIRVariable) and arg.non_ssa_version == param:
            if any(ret.is_storage for ret in callee.returns) or _may_write_storage_param(
                callee, callee_param, explored
            ):
                return True
    return False


def _state_variables_written_through_storage_args(function: Function) -> list[StateVariable]:
    """
    Return the state variables passed by storage reference to a call that may write them
    For example, a string state variable given to a library function that writes it through
    assembly (OpenZeppelin ShortStrings.toShortStringWithFallback)
    """
    written = []
    for callee, arg, param in _storage_param_calls(function):
        if isinstance(arg, StateIRVariable):
            state_variables = [arg.non_ssa_version]
        elif isinstance(arg, LocalIRVariable) and arg.is_storage:
            # Storage pointer aliasing a state variable
            state_variables = [
                r.non_ssa_version for r in arg.refers_to if isinstance(r, StateIRVariable)
            ]
        else:
            continue
        if state_variables and _may_write_storage_param(callee, param, set()):
            written.extend(state_variables)
    return written


class UnchangedStateVariables:
    """
    Find state variables that could be declared as constant or immutable (not written after deployment).
    """

    def __init__(self, compilation_unit: SlitherCompilationUnit) -> None:
        self.compilation_unit = compilation_unit
        self._constant_candidates: list[StateVariable] = []
        self._immutable_candidates: list[StateVariable] = []

    @property
    def immutable_candidates(self) -> list[StateVariable]:
        """Return the immutable candidates"""
        return self._immutable_candidates

    @property
    def constant_candidates(self) -> list[StateVariable]:
        """Return the constant candidates"""
        return self._constant_candidates

    def detect(self) -> None:
        """Detect state variables that could be constant or immutable"""
        for c in self.compilation_unit.contracts_derived:
            if c.is_signature_only():
                continue
            variables = []
            functions = []

            variables.append(c.storage_variables_ordered)
            functions.append(c.all_functions_called)

            valid_candidates: set[StateVariable] = {
                item for sublist in variables for item in sublist if _valid_candidate(item)
            }

            all_functions: list[Function] = list(
                {item1 for sublist in functions for item1 in sublist if isinstance(item1, Function)}
            )

            variables_written = []
            constructor_variables_written = []
            variables_initialized = []
            for f in all_functions:
                written = f.state_variables_written + _state_variables_written_through_storage_args(
                    f
                )
                if f.is_constructor_variables:
                    variables_initialized.extend(written)
                elif f.is_constructor:
                    constructor_variables_written.extend(written)
                else:
                    variables_written.extend(written)

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
