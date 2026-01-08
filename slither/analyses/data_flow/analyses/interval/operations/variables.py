from typing import Optional, TYPE_CHECKING

from slither.core.declarations.function import Function
from slither.core.expressions.literal import Literal
from slither.core.solidity_types.elementary_type import Int, Uint, ElementaryType, Byte

# Import for global Solidity variables
try:
    from slither.core.declarations.solidity_variables import (
        SolidityVariableComposed,
        SOLIDITY_VARIABLES_COMPOSED,
    )
except ImportError:
    SolidityVariableComposed = None
    SOLIDITY_VARIABLES_COMPOSED = {}
from slither.analyses.data_flow.analyses.interval.core.tracked_variable import (
    TrackedSMTVariable,
)
from slither.analyses.data_flow.analyses.interval.utils import IntervalSMTUtils
from slither.analyses.data_flow.smt_solver.types import Sort, SortKind
from slither.utils.integer_conversion import convert_string_to_int

if TYPE_CHECKING:
    from slither.analyses.data_flow.smt_solver.solver import SMTSolver
    from slither.analyses.data_flow.analyses.interval.analysis.domain import IntervalDomain


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

        # Create tracked variable for base parameter name (without initializing to 0 - parameters have full range)
        tracked_var = IntervalSMTUtils.create_tracked_variable(solver, param_name, param_type)
        if tracked_var is not None:
            # Use add_range_variable for initialization (doesn't mark as used)
            domain.state.add_range_variable(param_name, tracked_var)
            # Function parameters don't get initialized to 0 - they have full range

        # Also initialize the first SSA version (e.g., paramName|paramName_1) which is used in assignments
        base_var_name = getattr(param, "name", None)
        if base_var_name is not None:
            # Extract base name from canonical name if it exists (e.g., "newNumber" from "Counter.setNumber(uint256).newNumber")
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
                    # SSA version also has full range (not initialized to 0)


def initialize_state_variables_with_constants(
    solver: "SMTSolver", domain: "IntervalDomain", function: Function
) -> None:
    """Pre-initialize state variables that have constant initial values.

    For state variables like `bytes32 public data = 0x1234...`, we constrain
    the tracked variable to the constant value instead of using full range.
    """
    # Guard: function must have a contract
    if not hasattr(function, "contract") or function.contract is None:
        return

    contract = function.contract

    # Guard: contract must have state variables
    if not hasattr(contract, "state_variables") or not contract.state_variables:
        return

    # Process each state variable
    for state_var in contract.state_variables:
        # Guard: must have an initial expression (constant value)
        if not state_var.initialized or state_var.expression is None:
            continue

        # Guard: expression must be a literal (constant)
        expr = state_var.expression
        if not isinstance(expr, Literal):
            continue

        # Get the variable type
        var_type = IntervalSMTUtils.resolve_elementary_type(state_var.type, None)
        if var_type is None:
            continue

        # Guard: must be a supported type
        if IntervalSMTUtils.solidity_type_to_smt_sort(var_type) is None:
            continue

        # Get the constant value from the literal
        const_value = expr.converted_value
        # Handle hex strings (e.g., bytes32)
        if isinstance(const_value, str):
            try:
                const_value = convert_string_to_int(const_value)
            except (ValueError, TypeError):
                continue
        if not isinstance(const_value, int):
            continue

        # Build the canonical state variable name
        state_var_name = IntervalSMTUtils.resolve_variable_name(state_var)
        if state_var_name is None:
            continue

        # Create tracked variable if not exists
        tracked_var = IntervalSMTUtils.get_tracked_variable(domain, state_var_name)
        if tracked_var is None:
            tracked_var = IntervalSMTUtils.create_tracked_variable(solver, state_var_name, var_type)
            if tracked_var is None:
                continue
            domain.state.add_range_variable(state_var_name, tracked_var)

        # Constrain to the constant value
        const_term = solver.create_constant(const_value, tracked_var.sort)
        solver.assert_constraint(tracked_var.term == const_term)
        tracked_var.assert_no_overflow(solver)

        # Also initialize the SSA versions consumed by Phi (_0) and by first assignments (_1)
        base_var_name = getattr(state_var, "name", None)
        if base_var_name is not None:
            # Create and constrain the _0 version so Phi rvalues resolve (e.g., MAX_COUNT_0)
            first_ssa_zero_name = f"{state_var_name}|{base_var_name}_0"
            if not domain.state.has_range_variable(first_ssa_zero_name):
                ssa_zero_tracked = IntervalSMTUtils.create_tracked_variable(
                    solver, first_ssa_zero_name, var_type
                )
                # Ensure Phi can bind to the constant initializer
                if ssa_zero_tracked is not None:
                    domain.state.add_range_variable(first_ssa_zero_name, ssa_zero_tracked)
                    ssa_zero_const_term = solver.create_constant(const_value, ssa_zero_tracked.sort)
                    solver.assert_constraint(ssa_zero_tracked.term == ssa_zero_const_term)
                    ssa_zero_tracked.assert_no_overflow(solver)

            # Construct first SSA version name
            first_ssa_name = f"{state_var_name}|{base_var_name}_1"
            if not domain.state.has_range_variable(first_ssa_name):
                ssa_tracked = IntervalSMTUtils.create_tracked_variable(
                    solver, first_ssa_name, var_type
                )
                if ssa_tracked is not None:
                    domain.state.add_range_variable(first_ssa_name, ssa_tracked)
                    # Constrain SSA version to the same constant value
                    ssa_const_term = solver.create_constant(const_value, ssa_tracked.sort)
                    solver.assert_constraint(ssa_tracked.term == ssa_const_term)
                    ssa_tracked.assert_no_overflow(solver)
