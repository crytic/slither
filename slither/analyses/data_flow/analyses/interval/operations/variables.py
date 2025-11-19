from typing import Optional, TYPE_CHECKING

from slither.analyses.data_flow.analyses.interval.core.tracked_variable import (
    TrackedSMTVariable,
)
from slither.analyses.data_flow.analyses.interval.utils import IntervalSMTUtils

if TYPE_CHECKING:
    from slither.analyses.data_flow.smt_solver.solver import SMTSolver
    from slither.analyses.data_flow.analyses.interval.analysis.domain import IntervalDomain


def handle_variable_declaration(
    solver: "SMTSolver",
    domain: "IntervalDomain",
    variable,
) -> None:
    """Create a tracked SMT variable for a newly declared Solidity variable.

    At declaration, we only create the variable - we don't constrain its value.
    The solver will find all possible values that satisfy later constraints.
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

    # KEY FIX: Don't constrain the variable's value range here
    # Let the solver find any value that satisfies the constraints
    # The bitvector's bit-width already limits the range implicitly
