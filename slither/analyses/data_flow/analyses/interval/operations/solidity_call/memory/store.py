"""Handlers for memory store builtins (mstore, mstore8)."""

from typing import Optional, TYPE_CHECKING

from slither.analyses.data_flow.analyses.interval.operations.solidity_call.memory.base import (
    MemoryBaseHandler,
)
from slither.analyses.data_flow.analyses.interval.analysis.domain import (
    DomainVariant,
    IntervalDomain,
)
from slither.analyses.data_flow.analyses.interval.safety.memory_safety import (
    MemorySafetyChecker,
)
from slither.analyses.data_flow.analyses.interval.utils import IntervalSMTUtils
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.slithir.operations.solidity_call import SolidityCall

if TYPE_CHECKING:
    from slither.core.cfg.node import Node


class MemoryStoreHandler(MemoryBaseHandler):
    """Handle `mstore`/`mstore8` memory writes."""

    def __init__(self, solver=None, analysis=None, byte_size: int = 32) -> None:
        super().__init__(solver, analysis)
        self.byte_size = byte_size

    def handle(
        self,
        operation: Optional[SolidityCall],
        domain: "IntervalDomain",
        node: "Node",
    ) -> None:
        if not self._validate_preconditions(operation, domain):
            return

        offset_arg, value_arg = self._extract_arguments(operation)
        if offset_arg is None or value_arg is None:
            return

        self._check_memory_safety(offset_arg, value_arg, domain, node)

        slot_name = self._resolve_memory_slot_name(offset_arg, domain)
        if slot_name is None:
            return

        memory_type = self._determine_memory_type(value_arg)
        if memory_type is None:
            return

        memory_var = self._get_or_create_memory_var(domain, slot_name, memory_type)
        if memory_var is None:
            return

        self._apply_store_constraint(value_arg, memory_var, domain, memory_type)

    def _validate_preconditions(
        self, operation: Optional[SolidityCall], domain: "IntervalDomain"
    ) -> bool:
        """Validate operation, solver, and domain state."""
        if operation is None or not isinstance(operation, SolidityCall):
            return False
        if self.solver is None:
            return False
        if domain.variant != DomainVariant.STATE:
            return False
        return True

    def _extract_arguments(
        self, operation: SolidityCall
    ) -> tuple[Optional[object], Optional[object]]:
        """Extract offset and value arguments from operation."""
        if not operation.arguments or len(operation.arguments) < 2:
            return None, None
        return operation.arguments[0], operation.arguments[1]

    def _determine_memory_type(self, value_arg: object) -> Optional[ElementaryType]:
        """Determine the memory cell type based on store width or value type."""
        value_type = IntervalSMTUtils.resolve_elementary_type(getattr(value_arg, "type", None))
        memory_type = self._memory_elementary_type(self.byte_size)
        if value_type is not None and self.byte_size == 32:
            memory_type = value_type

        if IntervalSMTUtils.solidity_type_to_smt_sort(memory_type) is None:
            return None
        return memory_type

    def _get_or_create_memory_var(
        self, domain: "IntervalDomain", slot_name: str, memory_type: ElementaryType
    ):
        """Get existing or create new memory variable."""
        memory_var = IntervalSMTUtils.get_tracked_variable(domain, slot_name)
        if memory_var is not None:
            return memory_var

        memory_var = IntervalSMTUtils.create_tracked_variable(self.solver, slot_name, memory_type)
        if memory_var is None:
            return None
        domain.state.set_range_variable(slot_name, memory_var)
        return memory_var

    def _apply_store_constraint(
        self, value_arg: object, memory_var, domain: "IntervalDomain", memory_type: ElementaryType
    ) -> None:
        """Apply store constraint to memory variable."""
        value_term = self._resolve_value_term(value_arg, memory_var, domain, memory_type)
        if value_term is None:
            return

        self.solver.assert_constraint(memory_var.term == value_term)
        memory_var.assert_no_overflow(self.solver)

    def _check_memory_safety(
        self,
        offset_arg: object,
        value_arg: object,
        domain: "IntervalDomain",
        node: "Node",
    ) -> None:
        """Check memory store operation for safety violations.

        This detects vulnerabilities such as:
        - Memory underflow (write location < base pointer)
        - Arbitrary memory writes (unconstrained write location)
        - Overflow in pointer arithmetic
        """
        # Guard: need analysis context for safety checking
        if self.analysis is None:
            return

        # Guard: need solver for constraint checking
        if self.solver is None:
            return

        # Create a safety checker with the current context
        checker = MemorySafetyChecker(
            solver=self.solver,
            domain=domain,
            context=self.analysis.safety_context,
        )

        # Perform safety checks on the mstore operation
        violations = checker.check_mstore(offset_arg, value_arg, node)

        # Report violations to the analysis
        for violation in violations:
            self.analysis.add_safety_violation(violation)
            self.logger.warning(
                "Memory safety violation detected: {violation_type} - {details}",
                violation_type=violation.violation_type.value,
                details=violation.message,
            )

