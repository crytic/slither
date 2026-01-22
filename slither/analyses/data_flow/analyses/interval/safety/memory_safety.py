"""Memory safety property checker for detecting memory underflow vulnerabilities.

This module provides detection for memory safety violations where a computed
memory write location could be less than the base pointer due to arithmetic
overflow/underflow in pointer arithmetic.

Example vulnerability:
    let ptr := mload(0x40)           // Base pointer
    let offset := calldataload(...)  // Attacker-controlled
    let writeLocation := add(ptr, offset)  // Could underflow!
    mstore(writeLocation, ...)       // Writing before ptr is a vulnerability
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, TYPE_CHECKING

from slither.analyses.data_flow.analyses.interval.utils import IntervalSMTUtils
from slither.analyses.data_flow.logger import get_logger

if TYPE_CHECKING:
    from slither.analyses.data_flow.analyses.interval.analysis.domain import IntervalDomain
    from slither.analyses.data_flow.analyses.interval.core.tracked_variable import (
        TrackedSMTVariable,
    )
    from slither.analyses.data_flow.smt_solver.solver import SMTSolver
    from slither.analyses.data_flow.smt_solver.types import SMTTerm
    from slither.core.cfg.node import Node
    from slither.slithir.operations.solidity_call import SolidityCall


class ViolationType(Enum):
    """Type of memory safety violation."""

    MEMORY_UNDERFLOW = "memory_underflow"
    ARBITRARY_WRITE = "arbitrary_write"
    OVERFLOW_IN_POINTER_ARITHMETIC = "overflow_in_pointer_arithmetic"


@dataclass
class MemorySafetyViolation:
    """Represents a detected memory safety violation."""

    violation_type: ViolationType
    message: str
    write_location_name: str
    base_pointer_name: Optional[str] = None
    write_location_range: Optional[tuple[int, int]] = None
    base_pointer_range: Optional[tuple[int, int]] = None
    node: Optional["Node"] = None
    severity: str = "HIGH"
    recommendation: str = ""

    def __str__(self) -> str:
        parts = [f"[{self.severity}] {self.violation_type.value}: {self.message}"]
        if self.write_location_range:
            parts.append(
                f"  Write location '{self.write_location_name}' range: "
                f"[{self.write_location_range[0]}, {self.write_location_range[1]}]"
            )
        if self.base_pointer_range and self.base_pointer_name:
            parts.append(
                f"  Base pointer '{self.base_pointer_name}' range: "
                f"[{self.base_pointer_range[0]}, {self.base_pointer_range[1]}]"
            )
        if self.recommendation:
            parts.append(f"  Recommendation: {self.recommendation}")
        return "\n".join(parts)


@dataclass
class MemorySafetyContext:
    """Context for tracking memory operations and their base pointers."""

    # Maps write location variable names to their source expressions
    # e.g., "writeLocation" -> {"base": "ptr", "offsets": ["baseOffset", "userLength"]}
    pointer_arithmetic: Dict[str, Dict[str, object]] = field(default_factory=dict)

    # Tracks which variables came from mload(0x40) - the free memory pointer
    free_memory_pointers: set[str] = field(default_factory=set)

    # Tracks which variables came from calldataload (attacker-controlled)
    calldata_variables: set[str] = field(default_factory=set)


class MemorySafetyChecker:
    """
    Checks memory operations for safety property violations.

    This checker validates that:
    1. Memory write locations cannot underflow below the base pointer
    2. Pointer arithmetic doesn't allow arbitrary memory writes
    3. Attacker-controlled offsets are properly bounded

    Usage:
        checker = MemorySafetyChecker(solver, domain)
        violations = checker.check_mstore(operation, node)
        for v in violations:
            print(v)
    """

    # The EVM free memory pointer slot
    FREE_MEMORY_POINTER_SLOT = 0x40

    # Minimum valid free memory pointer value (after reserved slots)
    MIN_FREE_MEMORY_POINTER = 0x80

    def __init__(
        self,
        solver: "SMTSolver",
        domain: "IntervalDomain",
        context: Optional[MemorySafetyContext] = None,
    ) -> None:
        self.solver = solver
        self.domain = domain
        self.context = context or MemorySafetyContext()
        self.logger = get_logger()
        self._violations: List[MemorySafetyViolation] = []

    @property
    def violations(self) -> List[MemorySafetyViolation]:
        """Get all detected violations."""
        return self._violations

    def clear_violations(self) -> None:
        """Clear all detected violations."""
        self._violations.clear()

    def _apply_path_constraints(self) -> None:
        """Apply path constraints from the domain to the solver.
        
        Path constraints come from branch conditions (e.g., if baseOffset <= MAX_OFFSET).
        These must be applied before checking for violations to ensure we only detect
        violations that are possible given the current execution path.
        """
        path_constraints = self.domain.state.get_path_constraints()
        for constraint in path_constraints:
            self.solver.assert_constraint(constraint)
            self.logger.debug(
                "Applied path constraint to safety check: {constraint}",
                constraint=constraint,
            )

    def track_free_memory_pointer(self, var_name: str) -> None:
        """Mark a variable as containing the free memory pointer (from mload(0x40))."""
        self.context.free_memory_pointers.add(var_name)
        self.logger.debug(
            "Tracking free memory pointer variable: {var_name}",
            var_name=var_name,
        )

    def track_calldata_variable(self, var_name: str) -> None:
        """Mark a variable as attacker-controlled (from calldataload)."""
        self.context.calldata_variables.add(var_name)
        self.logger.debug(
            "Tracking calldata (attacker-controlled) variable: {var_name}",
            var_name=var_name,
        )

    def track_pointer_arithmetic(
        self,
        result_name: str,
        base_name: str,
        offset_names: List[str],
    ) -> None:
        """Track that a variable is computed from pointer + offset(s)."""
        self.context.pointer_arithmetic[result_name] = {
            "base": base_name,
            "offsets": offset_names,
        }
        self.logger.debug(
            "Tracking pointer arithmetic: {result} = {base} + {offsets}",
            result=result_name,
            base=base_name,
            offsets=offset_names,
        )

    def check_mstore(
        self,
        offset_arg: object,
        value_arg: object,
        node: Optional["Node"] = None,
    ) -> List[MemorySafetyViolation]:
        """
        Check an mstore operation for memory safety violations.

        Args:
            offset_arg: The memory offset argument (where to write)
            value_arg: The value being stored
            node: The CFG node containing this operation

        Returns:
            List of detected memory safety violations
        """
        violations: List[MemorySafetyViolation] = []

        offset_name = IntervalSMTUtils.resolve_variable_name(offset_arg)
        if offset_name is None:
            return violations

        # Get the tracked variable for the write location
        write_loc_var = IntervalSMTUtils.get_tracked_variable(self.domain, offset_name)
        if write_loc_var is None:
            return violations

        # Check 1: Does the write location have overflow in its computation?
        overflow_violation = self._check_overflow_in_write_location(
            offset_name, write_loc_var, node
        )
        if overflow_violation:
            violations.append(overflow_violation)
            self._violations.append(overflow_violation)

        # Check 2: Can the write location be below the expected base pointer?
        underflow_violation = self._check_memory_underflow(
            offset_name, write_loc_var, node
        )
        if underflow_violation:
            violations.append(underflow_violation)
            self._violations.append(underflow_violation)

        # Check 3: Is the write location computed from attacker-controlled data
        # without proper bounds checking?
        arbitrary_write_violation = self._check_arbitrary_write(
            offset_name, write_loc_var, node
        )
        if arbitrary_write_violation:
            violations.append(arbitrary_write_violation)
            self._violations.append(arbitrary_write_violation)

        return violations

    def _check_overflow_in_write_location(
        self,
        offset_name: str,
        write_loc_var: "TrackedSMTVariable",
        node: Optional["Node"],
    ) -> Optional[MemorySafetyViolation]:
        """Check if the write location computation could overflow due to attacker-controlled input."""
        from slither.analyses.data_flow.smt_solver.types import CheckSatResult

        # First check if this involves attacker-controlled data
        # Overflow with only constant offsets is not a security vulnerability
        arith_info = self.context.pointer_arithmetic.get(offset_name)
        if arith_info is not None:
            offsets = arith_info.get("offsets", [])
            attacker_controlled_offsets = [
                o for o in offsets if o in self.context.calldata_variables
            ]
            if not attacker_controlled_offsets:
                self.logger.debug(
                    "Skipping overflow check for '{name}': all offsets are constants or trusted",
                    name=offset_name,
                )
                return None

        # Check if overflow is possible
        self.solver.push()
        try:
            # Apply path constraints from the current execution path
            # (e.g., if we're past a bounds check, the offset is constrained)
            self._apply_path_constraints()

            # Assert that overflow occurred
            overflow_term = write_loc_var.overflow_flag.term
            self.solver.assert_constraint(overflow_term)

            result = self.solver.check_sat()
            if result == CheckSatResult.SAT:
                # Overflow is possible in the write location computation
                return MemorySafetyViolation(
                    violation_type=ViolationType.OVERFLOW_IN_POINTER_ARITHMETIC,
                    message=(
                        f"Overflow detected in write location computation for '{offset_name}'. "
                        "Large unsigned values can cause arithmetic wraparound."
                    ),
                    write_location_name=offset_name,
                    node=node,
                    severity="HIGH",
                    recommendation=(
                        "Add bounds checks on pointer offsets before arithmetic. "
                        "Example: require(offset < MAX_SAFE_OFFSET)"
                    ),
                )
        finally:
            self.solver.pop()

        return None

    def _check_memory_underflow(
        self,
        offset_name: str,
        write_loc_var: "TrackedSMTVariable",
        node: Optional["Node"],
    ) -> Optional[MemorySafetyViolation]:
        """
        Check if write location could be less than the base pointer.

        This is the key vulnerability detection: if writeLocation = ptr + offset,
        and offset is attacker-controlled (full uint256 range), then writeLocation
        could wrap around and be less than ptr.
        """
        from slither.analyses.data_flow.smt_solver.types import CheckSatResult, Sort, SortKind

        # Look for pointer arithmetic context
        arith_info = self.context.pointer_arithmetic.get(offset_name)
        if arith_info is None:
            # Try to find the base by checking if any free memory pointer variable
            # is involved in computing this value
            arith_info = self._infer_pointer_arithmetic(offset_name)

        if arith_info is None:
            # No pointer arithmetic context - check if write location can be
            # below the minimum valid memory region
            return self._check_write_below_minimum(offset_name, write_loc_var, node)

        base_name = arith_info.get("base")
        if base_name is None:
            return None

        # Check if any offsets are attacker-controlled
        offsets = arith_info.get("offsets", [])
        attacker_controlled_offsets = [
            o for o in offsets if o in self.context.calldata_variables
        ]

        # If no offsets are attacker-controlled, skip the underflow check.
        # Constant offsets (like 32, 64) cannot cause underflow - they only
        # add positive values to the base pointer.
        if not attacker_controlled_offsets:
            self.logger.debug(
                "Skipping underflow check for '{name}': all offsets are constants or trusted",
                name=offset_name,
            )
            return None

        base_var = IntervalSMTUtils.get_tracked_variable(self.domain, base_name)
        if base_var is None:
            return None

        # Check if writeLocation < base is satisfiable
        self.solver.push()
        try:
            # Apply path constraints from the current execution path
            self._apply_path_constraints()

            # Create the constraint: writeLocation < base
            underflow_condition = self.solver.bv_ult(
                write_loc_var.term, base_var.term
            )
            self.solver.assert_constraint(underflow_condition)

            result = self.solver.check_sat()
            if result == CheckSatResult.SAT:
                # Memory underflow is possible!
                # Get the actual ranges for reporting
                write_range = self._get_variable_range(write_loc_var)
                base_range = self._get_variable_range(base_var)

                message = (
                    f"Memory underflow: '{offset_name}' can be less than base pointer '{base_name}'. "
                    f"Attacker-controlled offset(s): {attacker_controlled_offsets}"
                )

                return MemorySafetyViolation(
                    violation_type=ViolationType.MEMORY_UNDERFLOW,
                    message=message,
                    write_location_name=offset_name,
                    base_pointer_name=base_name,
                    write_location_range=write_range,
                    base_pointer_range=base_range,
                    node=node,
                    severity="CRITICAL",
                    recommendation=(
                        "Add bounds checks to ensure writeLocation >= ptr. "
                        "Example: require(offset <= type(uint128).max)"
                    ),
                )
        finally:
            self.solver.pop()

        return None

    def _check_write_below_minimum(
        self,
        offset_name: str,
        write_loc_var: "TrackedSMTVariable",
        node: Optional["Node"],
    ) -> Optional[MemorySafetyViolation]:
        """Check if write location can be below minimum valid memory (0x80)."""
        from slither.analyses.data_flow.smt_solver.types import CheckSatResult, Sort, SortKind

        # Check if writeLocation < 0x80 is satisfiable
        self.solver.push()
        try:
            # Apply path constraints from the current execution path
            self._apply_path_constraints()

            min_valid = self.solver.create_constant(
                self.MIN_FREE_MEMORY_POINTER,
                write_loc_var.sort,
            )
            below_minimum = self.solver.bv_ult(write_loc_var.term, min_valid)
            self.solver.assert_constraint(below_minimum)

            result = self.solver.check_sat()
            if result == CheckSatResult.SAT:
                write_range = self._get_variable_range(write_loc_var)
                return MemorySafetyViolation(
                    violation_type=ViolationType.MEMORY_UNDERFLOW,
                    message=(
                        f"Write location '{offset_name}' can be below minimum valid "
                        f"memory address (0x{self.MIN_FREE_MEMORY_POINTER:x})."
                    ),
                    write_location_name=offset_name,
                    write_location_range=write_range,
                    node=node,
                    severity="HIGH",
                    recommendation=(
                        "Ensure write location is always >= 0x80 (after reserved slots)."
                    ),
                )
        finally:
            self.solver.pop()

        return None

    def _check_arbitrary_write(
        self,
        offset_name: str,
        write_loc_var: "TrackedSMTVariable",
        node: Optional["Node"],
    ) -> Optional[MemorySafetyViolation]:
        """
        Check if the write location allows arbitrary memory writes.

        This checks if the write location's range spans a significant portion
        of the memory space, indicating lack of proper bounds.
        """
        # Apply path constraints before getting the range
        self.solver.push()
        try:
            self._apply_path_constraints()
            write_range = self._get_variable_range(write_loc_var)
        finally:
            self.solver.pop()

        if write_range is None:
            return None

        min_val, max_val = write_range

        # If the range spans the entire uint256 space, it's an arbitrary write
        max_uint256 = (1 << 256) - 1
        range_size = max_val - min_val

        # Consider it arbitrary if it spans more than 2^128 values
        # (indicating essentially unconstrained)
        arbitrary_threshold = 1 << 128

        if range_size >= arbitrary_threshold:
            # Check if this involves attacker-controlled data
            arith_info = self.context.pointer_arithmetic.get(offset_name)
            if arith_info:
                offsets = arith_info.get("offsets", [])
                attacker_controlled = any(
                    o in self.context.calldata_variables for o in offsets
                )
                if attacker_controlled:
                    return MemorySafetyViolation(
                        violation_type=ViolationType.ARBITRARY_WRITE,
                        message=(
                            f"Arbitrary memory write: '{offset_name}' range spans "
                            f"[{min_val}, {max_val}] with attacker-controlled offsets."
                        ),
                        write_location_name=offset_name,
                        write_location_range=write_range,
                        node=node,
                        severity="CRITICAL",
                        recommendation=(
                            "Bound attacker-controlled offsets to prevent arbitrary writes. "
                            "Example: require(userLength < data.length)"
                        ),
                    )

        return None

    def _infer_pointer_arithmetic(self, var_name: str) -> Optional[Dict[str, object]]:
        """
        Try to infer pointer arithmetic context for a variable.

        This looks at binary operations in the domain state to reconstruct
        which variables were added together.
        """
        # Check if this variable name contains patterns suggesting it's from
        # pointer arithmetic with free memory pointer
        for fmp_name in self.context.free_memory_pointers:
            if fmp_name in var_name or "ptr" in var_name.lower():
                return {
                    "base": fmp_name,
                    "offsets": list(self.context.calldata_variables),
                }

        return None

    def _get_variable_range(
        self, tracked_var: "TrackedSMTVariable"
    ) -> Optional[tuple[int, int]]:
        """Get the min/max range for a tracked variable."""
        from z3 import Optimize, sat

        # Use Z3 optimization to find min/max
        try:
            term = tracked_var.term

            # Get min
            opt_min = Optimize()
            opt_min.set("timeout", 1000)
            if hasattr(self.solver, "solver"):
                for assertion in self.solver.solver.assertions():
                    opt_min.add(assertion)
            opt_min.minimize(term)
            if opt_min.check() != sat:
                return None
            model = opt_min.model()
            min_val = model.eval(term, model_completion=True).as_long()

            # Get max
            opt_max = Optimize()
            opt_max.set("timeout", 1000)
            if hasattr(self.solver, "solver"):
                for assertion in self.solver.solver.assertions():
                    opt_max.add(assertion)
            opt_max.maximize(term)
            if opt_max.check() != sat:
                return None
            model = opt_max.model()
            max_val = model.eval(term, model_completion=True).as_long()

            return (min_val, max_val)
        except Exception:
            return None
