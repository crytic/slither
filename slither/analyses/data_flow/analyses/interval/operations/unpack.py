"""Handler for Unpack operations (tuple element extraction) in interval analysis."""

from typing import TYPE_CHECKING, Optional

from slither.analyses.data_flow.analyses.interval.analysis.domain import (
    DomainVariant,
    IntervalDomain,
)
from slither.analyses.data_flow.analyses.interval.operations.base import BaseOperationHandler
from slither.analyses.data_flow.analyses.interval.utils import IntervalSMTUtils
from slither.analyses.data_flow.smt_solver.types import SMTTerm
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.slithir.operations.internal_call import InternalCall
from slither.slithir.operations.library_call import LibraryCall
from slither.slithir.operations.return_operation import Return
from slither.slithir.operations.unpack import Unpack
from slither.slithir.variables.constant import Constant

if TYPE_CHECKING:
    from slither.core.cfg.node import Node
    from slither.analyses.data_flow.analyses.interval.core.tracked_variable import (
        TrackedSMTVariable,
    )


class UnpackHandler(BaseOperationHandler):
    """Handle Unpack operations by extracting tuple elements and creating tracked variables."""

    def handle(
        self,
        operation: Optional[Unpack],
        domain: "IntervalDomain",
        node: "Node",
    ) -> None:
        if not self._validate_preconditions(operation, domain):
            return

        lvalue_info = self._resolve_lvalue_info(operation)
        if lvalue_info is None:
            return
        lvalue_name, return_type = lvalue_info

        lvalue_tracked = self._get_or_create_tracked(domain, lvalue_name, return_type)
        if lvalue_tracked is None:
            return

        self._try_constrain_from_source(operation, node, lvalue_tracked, domain)

    def _validate_preconditions(
        self, operation: Optional[Unpack], domain: "IntervalDomain"
    ) -> bool:
        """Validate operation, solver, and domain state."""
        if operation is None or not isinstance(operation, Unpack):
            return False
        if self.solver is None:
            return False
        if domain.variant != DomainVariant.STATE:
            return False
        return True

    def _resolve_lvalue_info(
        self, operation: Unpack
    ) -> Optional[tuple[str, ElementaryType]]:
        """Resolve lvalue name and return type from operation."""
        lvalue = operation.lvalue
        if lvalue is None:
            return None

        lvalue_name = IntervalSMTUtils.resolve_variable_name(lvalue)
        if lvalue_name is None:
            return None

        return_type = IntervalSMTUtils.resolve_elementary_type(getattr(lvalue, "type", None))
        if return_type is None:
            self.logger.debug(
                "Could not determine return type for unpack operation '{name}', skipping",
                name=lvalue_name,
            )
            return None

        if IntervalSMTUtils.solidity_type_to_smt_sort(return_type) is None:
            self.logger.debug(
                "Unsupported type for unpack operation '{name}', skipping",
                name=lvalue_name,
            )
            return None

        return lvalue_name, return_type

    def _get_or_create_tracked(
        self, domain: "IntervalDomain", lvalue_name: str, return_type: ElementaryType
    ) -> Optional["TrackedSMTVariable"]:
        """Get existing or create new tracked variable."""
        tracked = IntervalSMTUtils.get_tracked_variable(domain, lvalue_name)
        if tracked is not None:
            return tracked

        tracked = IntervalSMTUtils.create_tracked_variable(self.solver, lvalue_name, return_type)
        if tracked is None:
            return None
        domain.state.set_range_variable(lvalue_name, tracked)
        tracked.assert_no_overflow(self.solver)
        return tracked

    def _try_constrain_from_source(
        self,
        operation: Unpack,
        node: "Node",
        lvalue_tracked: "TrackedSMTVariable",
        domain: "IntervalDomain",
    ) -> None:
        """Try to constrain from source call, or log as unconstrained."""
        lvalue_name = lvalue_tracked.base.name
        tuple_var = operation.tuple
        tuple_name = IntervalSMTUtils.resolve_variable_name(tuple_var)

        source_call = self._find_tuple_source_call(node, tuple_var)
        if source_call is not None:
            element_value = self._extract_return_element(source_call, operation.index)
            if element_value is not None:
                self._constrain_unpacked_value(lvalue_tracked, element_value, domain, lvalue_name)
                return

        self._log_unconstrained(lvalue_name, tuple_name, operation.index)

    def _log_unconstrained(
        self, lvalue_name: str, tuple_name: Optional[str], index: int
    ) -> None:
        """Log unconstrained unpack operation."""
        if tuple_name is not None:
            self.logger.debug(
                "Unpacked element '{lvalue}' from tuple '{tuple}' at index {index} (unconstrained)",
                lvalue=lvalue_name,
                tuple=tuple_name,
                index=index,
            )
        else:
            self.logger.debug(
                "Unpacked element '{lvalue}' from tuple at index {index} (unconstrained)",
                lvalue=lvalue_name,
                index=index,
            )

    def _find_tuple_source_call(self, node: "Node", tuple_var) -> Optional[object]:
        """Find the call operation that created the tuple variable."""
        # Resolve the tuple name once for name-based matching
        tuple_name = IntervalSMTUtils.resolve_variable_name(tuple_var)

        def _matches_tuple(ir_lvalue) -> bool:
            # Prefer direct object identity
            if ir_lvalue == tuple_var:
                return True
            # Fall back to name-based match to handle SSA copies
            if tuple_name is None:
                return False
            ir_name = IntervalSMTUtils.resolve_variable_name(ir_lvalue)
            return ir_name == tuple_name

        # First, search through the current node's IR operations
        for ir in node.irs:
            if isinstance(ir, (InternalCall, LibraryCall)) and _matches_tuple(ir.lvalue):
                return ir

        # If not found in current node, search through all nodes in the function
        # (in case the call is in a different node)
        if node.function is not None:
            for func_node in node.function.nodes:
                for ir in func_node.irs:
                    if isinstance(ir, (InternalCall, LibraryCall)) and _matches_tuple(ir.lvalue):
                        return ir

        return None

    def _extract_return_element(self, call_operation: object, index: int) -> Optional[object]:
        """Extract the return value element at the given index from a call operation."""
        if not hasattr(call_operation, "function"):
            return None

        called_function = call_operation.function
        if called_function is None:
            return None

        # Find Return operations in the called function
        return_values = []
        for func_node in called_function.nodes:
            for ir in func_node.irs:
                if isinstance(ir, Return) and ir.values:
                    return_values.extend(ir.values)

        # Get the element at the specified index
        if 0 <= index < len(return_values):
            return return_values[index]

        return None

    def _constrain_unpacked_value(
        self,
        lvalue_tracked: "TrackedSMTVariable",
        element_value: object,
        domain: "IntervalDomain",
        lvalue_name: str,
    ) -> None:
        """Constrain the unpacked variable to equal the extracted element value."""
        if self.solver is None:
            return

        # Handle constant values
        if isinstance(element_value, Constant):
            constant_value = getattr(element_value, "value", None)
            if constant_value is not None:
                # Create a constant SMT term
                constant_term = self.solver.create_constant(constant_value, lvalue_tracked.sort)
                constraint: SMTTerm = lvalue_tracked.term == constant_term
                self.solver.assert_constraint(constraint)
                self.logger.debug(
                    "Constrained unpacked element '{name}' to constant value {value}",
                    name=lvalue_name,
                    value=constant_value,
                )
                return

        # Handle variable values - try to find the tracked variable
        element_name = IntervalSMTUtils.resolve_variable_name(element_value)
        if element_name is None:
            self.logger.debug(
                "Could not constrain unpacked element '{name}' - element value not trackable",
                name=lvalue_name,
            )
            return

        element_tracked = IntervalSMTUtils.get_tracked_variable(domain, element_name)
        if element_tracked is None:
            self.logger.debug(
                "Could not constrain unpacked element '{name}' - element value not trackable",
                name=lvalue_name,
            )
            return

        # Handle width mismatches
        lvalue_width = self.solver.bv_size(lvalue_tracked.term)
        element_width = self.solver.bv_size(element_tracked.term)

        if lvalue_width != element_width:
            # Handle width mismatch by extending or truncating
            if element_width < lvalue_width:
                is_signed = bool(element_tracked.base.metadata.get("is_signed", False))
                element_term = IntervalSMTUtils.extend_to_width(
                    self.solver, element_tracked.term, lvalue_width, is_signed
                )
            else:
                element_term = IntervalSMTUtils.truncate_to_width(
                    self.solver, element_tracked.term, lvalue_width
                )
            constraint: SMTTerm = lvalue_tracked.term == element_term
        else:
            constraint: SMTTerm = lvalue_tracked.term == element_tracked.term

        self.solver.assert_constraint(constraint)
        self.logger.debug(
            "Constrained unpacked element '{lvalue}' to variable '{element}'",
            lvalue=lvalue_name,
            element=element_name,
        )
