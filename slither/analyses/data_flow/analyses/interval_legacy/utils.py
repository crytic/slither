"""Utility helpers for interval SMT operations."""

from typing import Optional, TYPE_CHECKING, Union

from slither.core.solidity_types.elementary_type import ElementaryType, Int, Uint, Byte
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
    def is_signed_type(solidity_type: ElementaryType) -> bool:
        """Return True if the solidity type is a signed integer."""
        return solidity_type.type in Int

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
        """Create and declare a new tracked SMT variable for an elementary Solidity type."""
        sort = IntervalSMTUtils.solidity_type_to_smt_sort(solidity_type)
        if sort is None:
            return None
        tracked = TrackedSMTVariable.create(solver, name, sort)
        IntervalSMTUtils._annotate_tracked_variable(tracked, solidity_type)
        # Type bounds are now enforced by the bitvector width itself
        return tracked

    @staticmethod
    def _annotate_tracked_variable(
        tracked: TrackedSMTVariable, solidity_type: ElementaryType
    ) -> None:
        """Store useful metadata about the tracked variable."""
        tracked.base.metadata["solidity_type"] = solidity_type.type
        tracked.base.metadata["is_signed"] = IntervalSMTUtils.is_signed_type(solidity_type)
        width = IntervalSMTUtils.type_bit_width(solidity_type)
        tracked.base.metadata["bit_width"] = width
        bounds = IntervalSMTUtils.type_bounds(solidity_type)
        if bounds:
            tracked.base.metadata["min_value"], tracked.base.metadata["max_value"] = bounds

    @staticmethod
    def solidity_type_to_smt_sort(solidity_type: ElementaryType) -> Optional[Sort]:
        """Convert a Solidity elementary type into an SMT sort with appropriate bit width."""
        if solidity_type.type in Uint or solidity_type.type in Int:
            width = IntervalSMTUtils.type_bit_width(solidity_type)
            return Sort(kind=SortKind.BITVEC, parameters=[width])
        if solidity_type.type == "bool":
            # Use 1-bit bitvector for booleans
            return Sort(kind=SortKind.BITVEC, parameters=[1])
        if solidity_type.type == "address" or solidity_type.type == "address payable":
            # Use 160-bit bitvector for addresses
            return Sort(kind=SortKind.BITVEC, parameters=[160])
        if solidity_type.type in Byte:
            # For bytes types, use appropriate width
            width = IntervalSMTUtils.type_bit_width(solidity_type)
            return Sort(kind=SortKind.BITVEC, parameters=[width])
        return None

    @staticmethod
    def type_bit_width(solidity_type: ElementaryType) -> int:
        type_str = solidity_type.type
        if type_str in Uint:
            return 256 if type_str == "uint" else int(type_str.replace("uint", ""))
        if type_str in Int:
            return 256 if type_str == "int" else int(type_str.replace("int", ""))
        if type_str == "bool":
            return 1
        if type_str == "address" or type_str == "address payable":
            return 160
        if type_str in Byte:
            if type_str == "bytes":
                # Dynamic bytes: track length as uint256
                return 256
            if type_str.startswith("bytes") and type_str != "bytes":
                # Fixed-size bytes: N bytes = N*8 bits
                return int(type_str.replace("bytes", "")) * 8

        raise ValueError(f"Unsupported solidity type {type_str}")

    @staticmethod
    def type_bounds(solidity_type: ElementaryType) -> Optional[tuple[int, int]]:
        """Return the (min, max) bounds for the given Solidity elementary type."""
        type_str = solidity_type.type

        if type_str in Uint:
            return IntervalSMTUtils._uint_bounds(type_str)

        if type_str in Int:
            return IntervalSMTUtils._int_bounds(type_str)

        if type_str == "bool":
            return 0, 1

        if type_str in ("address", "address payable"):
            return 0, (1 << 160) - 1

        if type_str in Byte:
            return IntervalSMTUtils._byte_bounds(type_str)

        return None

    @staticmethod
    def _uint_bounds(type_str: str) -> tuple[int, int]:
        """Get bounds for unsigned integer type."""
        width = 256 if type_str == "uint" else int(type_str.replace("uint", ""))
        return 0, (1 << width) - 1

    @staticmethod
    def _int_bounds(type_str: str) -> tuple[int, int]:
        """Get bounds for signed integer type."""
        width = 256 if type_str == "int" else int(type_str.replace("int", ""))
        return -(1 << (width - 1)), (1 << (width - 1)) - 1

    @staticmethod
    def _byte_bounds(type_str: str) -> tuple[int, int]:
        """Get bounds for byte type."""
        if type_str == "bytes":
            return 0, (1 << 256) - 1
        if type_str == "byte":
            return 0, 255
        width = int(type_str.replace("bytes", "")) * 8
        return 0, (1 << width) - 1

    @staticmethod
    def create_constant_term(
        solver: "SMTSolver", value: Union[int, bool], solidity_type: Optional[ElementaryType]
    ):
        """Create a bitvector constant with the appropriate width for the Solidity type."""
        is_bool = isinstance(value, bool)
        logical_value = 1 if is_bool and value else 0 if is_bool else value

        if solidity_type is not None:
            width = IntervalSMTUtils.type_bit_width(solidity_type)
            signed = IntervalSMTUtils.is_signed_type(solidity_type)
        else:
            width = 1 if is_bool else 256
            signed = False

        modulus = 1 << width
        if signed:
            logical_value = logical_value % modulus
            if logical_value >= (1 << (width - 1)):
                logical_value -= modulus
        else:
            logical_value = logical_value % modulus

        if logical_value < 0:
            logical_value = (logical_value + modulus) % modulus

        return solver.create_constant(logical_value, Sort(kind=SortKind.BITVEC, parameters=[width]))

    @staticmethod
    def extend_to_width(solver: "SMTSolver", term, target_width: int, is_signed: bool):
        """Resize a bitvector term to a target width (extend or truncate as needed)."""
        current_width = solver.bv_size(term)
        if current_width == target_width:
            return term
        if current_width < target_width:
            # Extend
            extra_bits = target_width - current_width
            if is_signed:
                return solver.bv_sign_ext(term, extra_bits)
            return solver.bv_zero_ext(term, extra_bits)
        else:
            # Truncate - extract lower bits
            return solver.bv_extract(term, target_width - 1, 0)

    @staticmethod
    def truncate_to_width(solver: "SMTSolver", term, target_width: int):
        """Truncate a bitvector term to a target width by extracting lower bits."""
        current_width = solver.bv_size(term)
        if current_width <= target_width:
            return term
        return solver.bv_extract(term, target_width - 1, 0)

    @staticmethod
    def enforce_type_bounds(solver: "SMTSolver", tracked_var: "TrackedSMTVariable") -> None:
        """Enforce type bounds as solver constraints."""
        metadata = getattr(tracked_var.base, "metadata", {})
        min_value = metadata.get("min_value")
        max_value = metadata.get("max_value")

        if min_value is None and max_value is None:
            return

        term = tracked_var.term
        width = solver.bv_size(term)
        is_signed = metadata.get("is_signed", False)

        # Enforce minimum bound: term >= min_value
        if min_value is not None:
            min_const = solver.create_constant(
                min_value, Sort(kind=SortKind.BITVEC, parameters=[width])
            )
            # term >= min_value is equivalent to Not(term < min_value)
            if is_signed:
                # For signed: use signed comparison
                min_constraint = solver.Not(solver.bv_slt(term, min_const))
            else:
                # For unsigned: use unsigned comparison
                min_constraint = solver.Not(solver.bv_ult(term, min_const))
            solver.assert_constraint(min_constraint)

        # Enforce maximum bound: term <= max_value
        if max_value is not None:
            max_const = solver.create_constant(
                max_value, Sort(kind=SortKind.BITVEC, parameters=[width])
            )
            # term <= max_value is equivalent to Not(term > max_value)
            if is_signed:
                # For signed: use signed comparison
                max_constraint = solver.Not(solver.bv_slt(max_const, term))
            else:
                # For unsigned: use unsigned comparison
                max_constraint = solver.Not(solver.bv_ult(max_const, term))
            solver.assert_constraint(max_constraint)
