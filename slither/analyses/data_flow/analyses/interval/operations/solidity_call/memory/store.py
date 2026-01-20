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
        # Guard: only process SolidityCall operations.
        if operation is None or not isinstance(operation, SolidityCall):
            return

        # Guard: solver is required to build constraints.
        if self.solver is None:
            return

        # Guard: skip non-concrete states.
        if domain.variant != DomainVariant.STATE:
            return

        # Guard: need offset and value arguments to model the store.
        if not operation.arguments or len(operation.arguments) < 2:
            return

        offset_arg = operation.arguments[0]
        value_arg = operation.arguments[1]

        # Perform memory safety checks before the store
        self._check_memory_safety(offset_arg, value_arg, domain, node)

        slot_name = self._resolve_memory_slot_name(offset_arg, domain)
        # Guard: skip if we cannot resolve a stable memory slot name.
        if slot_name is None:
            return

        # Decide the memory cell type based on the store width or value type.
        value_type = IntervalSMTUtils.resolve_elementary_type(getattr(value_arg, "type", None))
        memory_type: ElementaryType = self._memory_elementary_type(self.byte_size)
        if value_type is not None and self.byte_size == 32:
            memory_type = value_type

        # Guard: ensure the memory type can be represented.
        if IntervalSMTUtils.solidity_type_to_smt_sort(memory_type) is None:
            return

        memory_var = IntervalSMTUtils.get_tracked_variable(domain, slot_name)
        if memory_var is None:
            memory_var = IntervalSMTUtils.create_tracked_variable(
                self.solver, slot_name, memory_type
            )
            # Guard: creation may fail for unsupported types.
            if memory_var is None:
                return
            domain.state.set_range_variable(slot_name, memory_var)

        value_term = self._resolve_value_term(value_arg, memory_var, domain, memory_type)
        # Guard: skip if the value cannot be modeled.
        if value_term is None:
            return

        # Constrain memory cell to the stored value.
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

