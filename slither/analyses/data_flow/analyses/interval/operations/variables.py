from typing import Optional, TYPE_CHECKING

from slither.core.solidity_types.elementary_type import Int, Uint
from slither.analyses.data_flow.analyses.interval.core.tracked_variable import (
    TrackedSMTVariable,
)
from slither.analyses.data_flow.analyses.interval.utils import IntervalSMTUtils
from slither.analyses.data_flow.smt_solver.types import Sort, SortKind

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

    existing: Optional[TrackedSMTVariable] = domain.state.get_range_variable(var_name)
    if existing is not None:
        return

    tracked_var = IntervalSMTUtils.create_tracked_variable(solver, var_name, var_type)
    if tracked_var is None:
        return
    domain.state.set_range_variable(var_name, tracked_var)

    # Declarations start with no overflow condition
    tracked_var.assert_no_overflow(solver)

    # Initialize variable to Solidity default value based on type:
    # - Integer types (uint, int): initialized to 0
    # - Boolean type (bool): initialized to false (0 in bitvector)
    type_str = var_type.type
    if type_str in Uint or type_str in Int or type_str == "bool":
        # Create a constant term with value 0 (default for integers and false for bool)
        zero_sort = Sort(kind=SortKind.BITVEC, parameters=[256])
        zero_constant = solver.create_constant(0, zero_sort)
        solver.assert_constraint(tracked_var.term == zero_constant)
