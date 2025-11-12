"""Utility helpers for interval SMT operations."""

from typing import Optional, TYPE_CHECKING, Union

from slither.core.solidity_types.elementary_type import ElementaryType, Int, Uint
from slither.core.variables.variable import Variable
from slither.slithir.variables.variable import SlithIRVariable
from slither.slithir.variables.constant import Constant
from slither.analyses.data_flow.smt_solver.types import Sort, SortKind
from slither.analyses.data_flow.analyses.interval.core.tracked_variable import TrackedSMTVariable

if TYPE_CHECKING:
    from slither.analyses.data_flow.smt_solver.solver import SMTSolver

if TYPE_CHECKING:
    from slither.analyses.data_flow.analyses.interval.analysis.domain import IntervalDomain


class IntervalSMTUtils:
    """Helper methods for interacting with SMT variables in interval analysis."""

    @staticmethod
    def resolve_variable_name(var: Union[Variable, SlithIRVariable, Constant]) -> Optional[str]:
        """Build a stable name combining canonical/name with SSA identifier."""
        canonical = getattr(var, "canonical_name", None)
        base_name = canonical or getattr(var, "name", None)
        ssa_name = getattr(var, "ssa_name", None)

        if base_name is None and ssa_name is None:
            return None

        if base_name is None:
            return ssa_name

        if ssa_name and ssa_name != base_name:
            return f"{base_name}|{ssa_name}"

        return base_name

    @staticmethod
    def resolve_elementary_type(
        primary: Optional[object], fallback: Optional[object] = None
    ) -> Optional[ElementaryType]:
        """Return the first available ElementaryType from the provided candidates."""
        for candidate in (primary, fallback):
            if isinstance(candidate, ElementaryType):
                return candidate
            if candidate is not None and hasattr(candidate, "type"):
                nested_type = getattr(candidate, "type")
                if isinstance(nested_type, ElementaryType):
                    return nested_type
        return None

    @staticmethod
    def get_tracked_variable(domain: "IntervalDomain", name: str) -> Optional[TrackedSMTVariable]:
        """Return an existing tracked SMT variable from the interval domain state."""
        return domain.state.get_range_variable(name)

    @staticmethod
    def create_tracked_variable(
        solver: "SMTSolver", name: str, solidity_type: ElementaryType
    ) -> Optional[TrackedSMTVariable]:
        """Create and declare a new tracked SMT variable for the provided elementary Solidity type."""
        sort = IntervalSMTUtils.solidity_type_to_smt_sort(solidity_type)
        if sort is None:
            return None
        return TrackedSMTVariable.create(solver, name, sort)

    @staticmethod
    def solidity_type_to_smt_sort(solidity_type: ElementaryType) -> Optional[Sort]:
        """Convert a Solidity elementary type into an SMT sort."""
        type_str = solidity_type.type

        if type_str in Uint:
            width = 256 if type_str == "uint" else int(type_str.replace("uint", ""))
            return Sort(kind=SortKind.BITVEC, parameters=[width])

        if type_str in Int:
            width = 256 if type_str == "int" else int(type_str.replace("int", ""))
            return Sort(kind=SortKind.BITVEC, parameters=[width])

        if type_str == "bool":
            return Sort(kind=SortKind.BOOL)

        return None
