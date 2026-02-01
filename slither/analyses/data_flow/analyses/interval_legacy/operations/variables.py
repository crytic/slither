from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

from slither.core.declarations.function import Function
from slither.core.expressions.literal import Literal
from slither.core.solidity_types.elementary_type import Int, Uint, ElementaryType
from slither.core.solidity_types.array_type import ArrayType

# Import for global Solidity variables
try:
    from slither.core.declarations.solidity_variables import (
        SolidityVariableComposed,
        SOLIDITY_VARIABLES_COMPOSED,
    )
except ImportError:
    SolidityVariableComposed = None
    SOLIDITY_VARIABLES_COMPOSED = {}
from slither.analyses.data_flow.analyses.interval.utils import IntervalSMTUtils
from slither.utils.integer_conversion import convert_string_to_int

if TYPE_CHECKING:
    from slither.analyses.data_flow.smt_solver.solver import SMTSolver
    from slither.analyses.data_flow.analyses.interval.analysis.domain import IntervalDomain
    from slither.analyses.data_flow.analyses.interval.core.tracked_variable import (
        TrackedSMTVariable,
    )


@dataclass
class StateVarInfo:
    """Info about a state variable being initialized."""

    var: object
    name: str
    type: object
    const_value: int


def handle_variable_declaration(
    solver: "SMTSolver",
    domain: "IntervalDomain",
    variable,
) -> None:
    """Create a tracked SMT variable for a newly declared Solidity variable.

    At declaration, variables are initialized to their Solidity default values:
    - Integer types (uint, int): initialized to 0
    - Boolean type (bool): initialized to false
    """
    var_name = IntervalSMTUtils.resolve_variable_name(variable)
    if var_name is None:
        return

    var_type = IntervalSMTUtils.resolve_elementary_type(variable.type, None)
    if var_type is None:
        return

    # Use has_range_variable to avoid marking as used during declaration check
    if domain.state.has_range_variable(var_name):
        return

    tracked_var = IntervalSMTUtils.create_tracked_variable(solver, var_name, var_type)
    if tracked_var is None:
        return

    domain.state.set_range_variable(var_name, tracked_var)
    tracked_var.assert_no_overflow(solver)

    # Initialize variable to Solidity default value based on type:
    # - Integer types (uint, int): initialized to 0
    # - Boolean type (bool): initialized to false (0 in bitvector)
    # - Address type: initialized to 0 (zero address)
    type_str = var_type.type
    if (
        type_str not in Uint
        and type_str not in Int
        and type_str != "bool"
        and type_str != "address"
        and type_str != "address payable"
    ):
        return

    # Create a constant term with value 0 using the variable's sort (type-specific width)
    zero_constant = solver.create_constant(0, tracked_var.sort)
    solver.assert_constraint(tracked_var.term == zero_constant)

    # Also set the constraint on the first SSA version (value_0) if the base name was used
    # This ensures that when value_0 is used in comparisons, it has the = 0 constraint
    if "|" in var_name:
        # Already an SSA version, constraint is already set
        return

    # Base variable name - also create and constrain the first SSA version
    base_var_name = getattr(variable, "name", None)
    if base_var_name is None:
        return

    # Construct the SSA version name: baseName_0
    ssa_var_name = f"{var_name}|{base_var_name}_0"
    ssa_tracked = IntervalSMTUtils.get_tracked_variable(domain, ssa_var_name)
    if ssa_tracked is not None:
        return

    ssa_tracked = IntervalSMTUtils.create_tracked_variable(solver, ssa_var_name, var_type)
    if ssa_tracked is None:
        return

    domain.state.set_range_variable(ssa_var_name, ssa_tracked)
    ssa_tracked.assert_no_overflow(solver)
    # Set the same initial value constraint on SSA version
    solver.assert_constraint(ssa_tracked.term == zero_constant)


def initialize_global_solidity_variables(solver: "SMTSolver", domain: "IntervalDomain") -> None:
    """Pre-initialize global Solidity variables in the domain."""
    if SolidityVariableComposed is None:
        return

    # Initialize common global Solidity variables that are frequently used
    # These should have their full type range (not initialized to 0)
    # Only initialize elementary types (address, uint256, etc.)
    global_vars_to_init = [
        "msg.sender",  # address
        "msg.value",  # uint256
        "block.timestamp",  # uint256
        "block.number",  # uint256
        "block.coinbase",  # address
        "block.difficulty",  # uint256
        "block.gaslimit",  # uint256
        "block.chainid",  # uint256
        "tx.origin",  # address
        "tx.gasprice",  # uint256
    ]

    for var_name in global_vars_to_init:
        if var_name not in SOLIDITY_VARIABLES_COMPOSED:
            continue

        # Check if already exists (shouldn't happen, but be safe)
        # Use has_range_variable to avoid marking as used during initialization
        if domain.state.has_range_variable(var_name):
            continue

        # Get the type for this global variable
        var_type_str = SOLIDITY_VARIABLES_COMPOSED[var_name]
        try:
            var_type = ElementaryType(var_type_str)
        except Exception:
            # Skip non-elementary types (like bytes, string)
            continue

        # Create tracked variable (without initializing to 0 - globals have full range)
        tracked_var = IntervalSMTUtils.create_tracked_variable(solver, var_name, var_type)
        if tracked_var is not None:
            # Use add_range_variable for initialization (doesn't mark as used)
            domain.state.add_range_variable(var_name, tracked_var)
            # Global variables don't get initialized to 0 - they have full range


def initialize_function_parameters(
    solver: "SMTSolver", domain: "IntervalDomain", function: Function
) -> None:
    """Pre-initialize function parameters in the domain with full possible ranges."""
    if not hasattr(function, "parameters") or not function.parameters:
        return

    # Initialize each function parameter with full range
    for param in function.parameters:
        param_name = IntervalSMTUtils.resolve_variable_name(param)
        if param_name is None:
            continue

        param_type = IntervalSMTUtils.resolve_elementary_type(param.type, None)
        if param_type is None:
            continue

        # Create tracked variable for base parameter name (params have full range)
        tracked_var = IntervalSMTUtils.create_tracked_variable(solver, param_name, param_type)
        if tracked_var is not None:
            # Use add_range_variable for initialization (doesn't mark as used)
            domain.state.add_range_variable(param_name, tracked_var)
            # Function parameters have no overflow - they are input values
            tracked_var.assert_no_overflow(solver)

        # Also initialize the first SSA version (e.g., name|name_1) for assignments
        base_var_name = getattr(param, "name", None)
        if base_var_name is not None:
            # Extract base name from canonical name (e.g., "foo" from "A.f(uint).foo")
            if "." in param_name:
                base_var_name = param_name.split(".")[-1]
            # Construct first SSA version name: canonicalName|baseName_1
            first_ssa_name = f"{param_name}|{base_var_name}_1"
            # Check if already exists
            if not domain.state.has_range_variable(first_ssa_name):
                ssa_tracked = IntervalSMTUtils.create_tracked_variable(
                    solver, first_ssa_name, param_type
                )
                if ssa_tracked is not None:
                    domain.state.add_range_variable(first_ssa_name, ssa_tracked)
                    # SSA version also has no overflow
                    ssa_tracked.assert_no_overflow(solver)


def initialize_state_variables_with_constants(
    solver: "SMTSolver", domain: "IntervalDomain", function: Function
) -> None:
    """Pre-initialize state variables that have constant initial values."""
    state_vars = _get_state_variables(function)
    if not state_vars:
        return

    for state_var in state_vars:
        _initialize_constant_state_var(solver, domain, state_var)


def _get_state_variables(function: Function) -> list:
    """Get state variables from function's contract."""
    if not hasattr(function, "contract") or function.contract is None:
        return []
    contract = function.contract
    if not hasattr(contract, "state_variables") or not contract.state_variables:
        return []
    return contract.state_variables


def _initialize_constant_state_var(
    solver: "SMTSolver", domain: "IntervalDomain", state_var
) -> None:
    """Initialize a single state variable with its constant value."""
    if not state_var.initialized or state_var.expression is None:
        return
    if not isinstance(state_var.expression, Literal):
        return

    var_type = IntervalSMTUtils.resolve_elementary_type(state_var.type, None)
    if var_type is None or IntervalSMTUtils.solidity_type_to_smt_sort(var_type) is None:
        return

    const_value = _get_constant_value(state_var.expression)
    if const_value is None:
        return

    state_var_name = IntervalSMTUtils.resolve_variable_name(state_var)
    if state_var_name is None:
        return

    tracked_var = _get_or_create_state_var(solver, domain, state_var_name, var_type)
    if tracked_var is None:
        return

    _constrain_to_constant(solver, tracked_var, const_value)
    var_info = StateVarInfo(state_var, state_var_name, var_type, const_value)
    _initialize_ssa_versions(solver, domain, var_info)


def _get_constant_value(expr: Literal) -> Optional[int]:
    """Extract integer constant value from literal."""
    const_value = expr.converted_value
    if isinstance(const_value, str):
        try:
            const_value = convert_string_to_int(const_value)
        except (ValueError, TypeError):
            return None
    if not isinstance(const_value, int):
        return None
    return const_value


def _get_or_create_state_var(
    solver: "SMTSolver", domain: "IntervalDomain", name: str, var_type
) -> Optional["TrackedSMTVariable"]:
    """Get or create tracked variable for state variable."""
    tracked_var = IntervalSMTUtils.get_tracked_variable(domain, name)
    if tracked_var is not None:
        return tracked_var

    tracked_var = IntervalSMTUtils.create_tracked_variable(solver, name, var_type)
    if tracked_var is None:
        return None

    domain.state.add_range_variable(name, tracked_var)
    return tracked_var


def _constrain_to_constant(solver: "SMTSolver", tracked_var, const_value: int) -> None:
    """Constrain tracked variable to constant value."""
    const_term = solver.create_constant(const_value, tracked_var.sort)
    solver.assert_constraint(tracked_var.term == const_term)
    tracked_var.assert_no_overflow(solver)


def _initialize_ssa_versions(
    solver: "SMTSolver",
    domain: "IntervalDomain",
    var_info: StateVarInfo,
) -> None:
    """Initialize SSA versions (_0 and _1) for state variable."""
    base_var_name = getattr(var_info.var, "name", None)
    if base_var_name is None:
        return

    for suffix in ("_0", "_1"):
        ssa_name = f"{var_info.name}|{base_var_name}{suffix}"
        if domain.state.has_range_variable(ssa_name):
            continue

        ssa_tracked = IntervalSMTUtils.create_tracked_variable(solver, ssa_name, var_info.type)
        if ssa_tracked is not None:
            domain.state.add_range_variable(ssa_name, ssa_tracked)
            _constrain_to_constant(solver, ssa_tracked, var_info.const_value)


def initialize_fixed_length_arrays(
    solver: "SMTSolver", domain: "IntervalDomain", function: Function
) -> None:
    """Pre-initialize all elements of fixed-length array state variables."""
    state_vars = _get_state_variables(function)
    if not state_vars:
        return

    for state_var in state_vars:
        _initialize_fixed_array(solver, domain, state_var)


def _initialize_fixed_array(
    solver: "SMTSolver", domain: "IntervalDomain", state_var
) -> None:
    """Initialize a single fixed-length array."""
    array_info = _get_fixed_array_info(state_var)
    if array_info is None:
        return

    array_var_name, array_length, element_type = array_info

    for i in range(array_length):
        _initialize_array_element(solver, domain, array_var_name, i, element_type)


def _get_fixed_array_info(state_var) -> Optional[tuple[str, int, ElementaryType]]:
    """Get info for a fixed-length array state variable."""
    if not isinstance(state_var.type, ArrayType):
        return None

    array_type = state_var.type
    if not array_type.is_fixed_array or array_type.length_value is None:
        return None

    try:
        array_length = int(str(array_type.length_value))
    except (ValueError, TypeError):
        return None

    element_type = IntervalSMTUtils.resolve_elementary_type(array_type.type)
    if element_type is None:
        return None
    if IntervalSMTUtils.solidity_type_to_smt_sort(element_type) is None:
        return None

    array_var_name = IntervalSMTUtils.resolve_variable_name(state_var)
    if array_var_name is None:
        return None

    return array_var_name, array_length, element_type


def _initialize_array_element(
    solver: "SMTSolver",
    domain: "IntervalDomain",
    array_var_name: str,
    index: int,
    element_type: ElementaryType,
) -> None:
    """Initialize a single array element."""
    element_name = f"{array_var_name}[{index}]"
    if domain.state.has_range_variable(element_name):
        return

    tracked_var = IntervalSMTUtils.create_tracked_variable(solver, element_name, element_type)
    if tracked_var is None:
        return

    domain.state.add_range_variable(element_name, tracked_var)
    tracked_var.assert_no_overflow(solver)
