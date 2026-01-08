"""Handler for Index operations (array indexing) in interval analysis."""

from typing import TYPE_CHECKING, Optional

from slither.analyses.data_flow.analyses.interval.analysis.domain import (
    DomainVariant,
    IntervalDomain,
)
from slither.analyses.data_flow.analyses.interval.operations.base import BaseOperationHandler
from slither.analyses.data_flow.analyses.interval.utils import IntervalSMTUtils
from slither.analyses.data_flow.smt_solver.types import CheckSatResult, SMTTerm, Sort, SortKind
from slither.core.solidity_types.array_type import ArrayType
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.slithir.operations.index import Index
from slither.slithir.variables.constant import Constant

if TYPE_CHECKING:
    from slither.core.cfg.node import Node


class IndexHandler(BaseOperationHandler):
    """Handle Index operations by tracking array element accesses and constraining reference variables to equal array elements."""

    def handle(
        self,
        operation: Optional[Index],
        domain: "IntervalDomain",
        node: "Node",
    ) -> None:
        # Guard: ensure we have a valid Index operation
        if operation is None or not isinstance(operation, Index):
            return

        # Guard: solver is required to create SMT variables
        if self.solver is None:
            return

        # Guard: only update when we have a concrete state domain
        if domain.variant != DomainVariant.STATE:
            return

        lvalue = operation.lvalue
        # Guard: nothing to track if there is no lvalue for the index reference
        if lvalue is None:
            return

        lvalue_name = IntervalSMTUtils.resolve_variable_name(lvalue)
        # Guard: skip if we cannot resolve a stable name for the reference
        if lvalue_name is None:
            return

        # Get the array variable and index value
        array_var = operation.variable_left
        index_value = operation.variable_right

        # Use canonical array name without SSA version for element tracking
        # (e.g., "Index.fixedArray" not "Index.fixedArray|fixedArray_0")
        array_var_name = IntervalSMTUtils.resolve_variable_name(array_var)
        if array_var_name is None:
            return

        # Strip SSA version suffix if present (e.g., "Index.fixedArray|fixedArray_0" -> "Index.fixedArray")
        if "|" in array_var_name:
            array_var_name = array_var_name.split("|")[0]

        # Build the index string representation
        # For constants, use the literal value; for variables, use the variable name
        if isinstance(index_value, Constant):
            index_str = str(index_value.value)
        else:
            index_var_name = IntervalSMTUtils.resolve_variable_name(index_value)
            if index_var_name is None:
                # Cannot resolve index variable name, skip
                return
            # Also strip SSA version from index variable name
            if "|" in index_var_name:
                index_var_name = index_var_name.split("|")[0]
            index_str = index_var_name

        # Build the array element variable name (e.g., "arr[0]" or "arr[i]")
        array_element_name = f"{array_var_name}[{index_str}]"

        # Resolve the type for the array element
        return_type: Optional[ElementaryType] = None

        # Prefer type from lvalue
        if hasattr(lvalue, "type"):
            return_type = IntervalSMTUtils.resolve_elementary_type(lvalue.type)

        # Guard: skip if we cannot determine a supported return type
        if return_type is None:
            return

        if IntervalSMTUtils.solidity_type_to_smt_sort(return_type) is None:
            # Guard: unsupported type for interval tracking
            return

        # Get or create tracked variable for the array element
        array_element_tracked = IntervalSMTUtils.get_tracked_variable(domain, array_element_name)
        if array_element_tracked is None:
            # Create a fresh tracked variable for the array element
            array_element_tracked = IntervalSMTUtils.create_tracked_variable(
                self.solver,
                array_element_name,
                return_type,
            )
            # Guard: creation may fail for unsupported types
            if array_element_tracked is None:
                return
            domain.state.set_range_variable(array_element_name, array_element_tracked)
            array_element_tracked.assert_no_overflow(self.solver)
            # Note: Array elements are NOT initialized to 0 here because we need to allow
            # assignments to update their values. The value will be set by the assignment handler.

        # Get or create tracked variable for the reference (lvalue)
        lvalue_tracked = IntervalSMTUtils.get_tracked_variable(domain, lvalue_name)
        if lvalue_tracked is None:
            # Create a fresh tracked variable for the reference
            lvalue_tracked = IntervalSMTUtils.create_tracked_variable(
                self.solver,
                lvalue_name,
                return_type,
            )
            # Guard: creation may fail for unsupported types
            if lvalue_tracked is None:
                return
            domain.state.set_range_variable(lvalue_name, lvalue_tracked)
            lvalue_tracked.assert_no_overflow(self.solver)

        # Constrain the reference to equal the array element value
        # This models: REF -> array[index] (reading from array element)
        lvalue_width = self.solver.bv_size(lvalue_tracked.term)
        element_width = self.solver.bv_size(array_element_tracked.term)

        if lvalue_width != element_width:
            # Handle width mismatch by extending or truncating
            if element_width < lvalue_width:
                is_signed = bool(array_element_tracked.base.metadata.get("is_signed", False))
                element_term = IntervalSMTUtils.extend_to_width(
                    self.solver, array_element_tracked.term, lvalue_width, is_signed
                )
            else:
                element_term = IntervalSMTUtils.truncate_to_width(
                    self.solver, array_element_tracked.term, lvalue_width
                )
            constraint: SMTTerm = lvalue_tracked.term == element_term
        else:
            constraint: SMTTerm = lvalue_tracked.term == array_element_tracked.term

        self.solver.assert_constraint(constraint)
        self.logger.debug(
            "Constrained index reference '{lvalue}' to equal array element '{element}'",
            lvalue=lvalue_name,
            element=array_element_name,
        )

        # Add bounds checking for fixed-length arrays with variable index
        if not isinstance(index_value, Constant):
            self._add_bounds_check(array_var, index_value, domain)

    def _add_bounds_check(
        self,
        array_var: object,
        index_value: object,
        domain: "IntervalDomain",
    ) -> None:
        """Add constraint that index < array_length for fixed-length arrays."""
        if self.solver is None:
            return

        # Get the array type
        array_type = getattr(array_var, "type", None)
        if array_type is None:
            return

        # Check if it's a fixed-length array
        if not isinstance(array_type, ArrayType):
            return

        if not array_type.is_fixed_array:
            return

        # Get the array length
        if array_type.length_value is None:
            return

        try:
            array_length = int(str(array_type.length_value))
        except (ValueError, TypeError):
            return

        # Get the index tracked variable
        index_name = IntervalSMTUtils.resolve_variable_name(index_value)
        if index_name is None:
            return

        index_tracked = IntervalSMTUtils.get_tracked_variable(domain, index_name)
        if index_tracked is None:
            # Try to create one
            index_type = getattr(index_value, "type", None)
            index_elem_type = IntervalSMTUtils.resolve_elementary_type(index_type)
            if index_elem_type is None:
                return
            index_tracked = IntervalSMTUtils.create_tracked_variable(
                self.solver, index_name, index_elem_type
            )
            if index_tracked is None:
                return
            domain.state.set_range_variable(index_name, index_tracked)

        # Check if out-of-bounds access is possible before constraining
        index_width = self.solver.bv_size(index_tracked.term)
        length_const = self.solver.create_constant(
            array_length, Sort(kind=SortKind.BITVEC, parameters=[index_width])
        )

        # Check if index >= length is satisfiable (potential out-of-bounds)
        in_bounds = self.solver.bv_ult(index_tracked.term, length_const)
        out_of_bounds = self.solver.Not(in_bounds)

        # Use push/pop to temporarily check without permanently adding constraints
        self.solver.push()
        self.solver.assert_constraint(out_of_bounds)
        oob_possible = self.solver.check_sat() == CheckSatResult.SAT
        self.solver.pop()

        if oob_possible:
            self.logger.warning(
                "⚠️  POTENTIAL OUT-OF-BOUNDS: '{index}' could be >= {length} (array length)",
                index=index_name,
                length=array_length,
            )

        # Add constraint: index < array_length for sound analysis
        bounds_constraint = self.solver.bv_ult(index_tracked.term, length_const)
        self.solver.assert_constraint(bounds_constraint)

        self.logger.debug(
            "Added bounds constraint: '{index}' < {length} for fixed-length array",
            index=index_name,
            length=array_length,
        )
