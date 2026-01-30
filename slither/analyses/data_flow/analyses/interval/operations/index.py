"""Handler for Index operations (array indexing) in interval analysis."""

from typing import TYPE_CHECKING, Optional, Tuple

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
    from slither.analyses.data_flow.analyses.interval.core.tracked_variable import (
        TrackedSMTVariable,
    )
    from slither.core.cfg.node import Node


class IndexHandler(BaseOperationHandler):
    """Handle Index operations by tracking array element accesses and constraining refs."""

    def handle(
        self,
        operation: Optional[Index],
        domain: "IntervalDomain",
        node: "Node",
    ) -> None:
        if not self._validate_operation(operation, domain):
            return

        names = self._extract_names(operation)
        if names is None:
            return
        lvalue_name, array_element_name, return_type = names

        element_var = self._get_or_create_element_var(
            array_element_name, return_type, domain
        )
        if element_var is None:
            return

        lvalue_var = self._get_or_create_lvalue_var(lvalue_name, return_type, domain)
        if lvalue_var is None:
            return

        self._constrain_lvalue_to_element(lvalue_var, element_var, lvalue_name, array_element_name)

        # Add bounds checking for fixed-length arrays with variable index
        index_value = operation.variable_right
        if not isinstance(index_value, Constant):
            self._add_bounds_check(operation.variable_left, index_value, domain)

    def _validate_operation(
        self, operation: Optional[Index], domain: "IntervalDomain"
    ) -> bool:
        """Validate the operation can be processed."""
        if operation is None or not isinstance(operation, Index):
            return False
        if self.solver is None:
            return False
        if domain.variant != DomainVariant.STATE:
            return False
        if operation.lvalue is None:
            return False
        return True

    def _extract_names(
        self, operation: Index
    ) -> Optional[Tuple[str, str, ElementaryType]]:
        """Extract lvalue name, array element name, and return type."""
        lvalue = operation.lvalue
        lvalue_name = IntervalSMTUtils.resolve_variable_name(lvalue)
        if lvalue_name is None:
            return None

        array_var = operation.variable_left
        index_value = operation.variable_right

        array_var_name = IntervalSMTUtils.resolve_variable_name(array_var)
        if array_var_name is None:
            return None

        # Strip SSA version suffix
        if "|" in array_var_name:
            array_var_name = array_var_name.split("|")[0]

        # Build index string
        if isinstance(index_value, Constant):
            index_str = str(index_value.value)
        else:
            index_var_name = IntervalSMTUtils.resolve_variable_name(index_value)
            if index_var_name is None:
                return None
            if "|" in index_var_name:
                index_var_name = index_var_name.split("|")[0]
            index_str = index_var_name

        array_element_name = f"{array_var_name}[{index_str}]"

        # Resolve return type
        return_type: Optional[ElementaryType] = None
        if hasattr(lvalue, "type"):
            return_type = IntervalSMTUtils.resolve_elementary_type(lvalue.type)

        if return_type is None:
            return None
        if IntervalSMTUtils.solidity_type_to_smt_sort(return_type) is None:
            return None

        return (lvalue_name, array_element_name, return_type)

    def _get_or_create_element_var(
        self,
        array_element_name: str,
        return_type: ElementaryType,
        domain: "IntervalDomain",
    ) -> Optional["TrackedSMTVariable"]:
        """Get or create tracked variable for array element."""
        tracked = IntervalSMTUtils.get_tracked_variable(domain, array_element_name)
        if tracked is not None:
            return tracked

        tracked = IntervalSMTUtils.create_tracked_variable(
            self.solver, array_element_name, return_type
        )
        if tracked is None:
            return None

        domain.state.set_range_variable(array_element_name, tracked)
        tracked.assert_no_overflow(self.solver)
        return tracked

    def _get_or_create_lvalue_var(
        self,
        lvalue_name: str,
        return_type: ElementaryType,
        domain: "IntervalDomain",
    ) -> Optional["TrackedSMTVariable"]:
        """Get or create tracked variable for lvalue reference."""
        tracked = IntervalSMTUtils.get_tracked_variable(domain, lvalue_name)
        if tracked is not None:
            return tracked

        tracked = IntervalSMTUtils.create_tracked_variable(
            self.solver, lvalue_name, return_type
        )
        if tracked is None:
            return None

        domain.state.set_range_variable(lvalue_name, tracked)
        tracked.assert_no_overflow(self.solver)
        return tracked

    def _constrain_lvalue_to_element(
        self,
        lvalue_var: "TrackedSMTVariable",
        element_var: "TrackedSMTVariable",
        lvalue_name: str,
        element_name: str,
    ) -> None:
        """Constrain the reference to equal the array element value."""
        lvalue_width = self.solver.bv_size(lvalue_var.term)
        element_width = self.solver.bv_size(element_var.term)

        if lvalue_width != element_width:
            element_term = self._adjust_width(element_var, lvalue_width)
            constraint: SMTTerm = lvalue_var.term == element_term
        else:
            constraint: SMTTerm = lvalue_var.term == element_var.term

        self.solver.assert_constraint(constraint)
        self.logger.debug(
            "Constrained index reference '{lvalue}' to equal array element '{element}'",
            lvalue=lvalue_name,
            element=element_name,
        )

    def _adjust_width(
        self, var: "TrackedSMTVariable", target_width: int
    ) -> SMTTerm:
        """Extend or truncate bitvector to match target width."""
        current_width = self.solver.bv_size(var.term)
        if current_width < target_width:
            is_signed = bool(var.base.metadata.get("is_signed", False))
            return IntervalSMTUtils.extend_to_width(
                self.solver, var.term, target_width, is_signed
            )
        return IntervalSMTUtils.truncate_to_width(self.solver, var.term, target_width)

    def _add_bounds_check(
        self, array_var: object, index_value: object, domain: "IntervalDomain"
    ) -> None:
        """Add constraint that index < array_length for fixed-length arrays."""
        length = self._get_fixed_array_length(array_var)
        if length is None:
            return

        index_tracked = self._get_or_create_index_var(index_value, domain)
        if index_tracked is None:
            return

        index_name = IntervalSMTUtils.resolve_variable_name(index_value)
        self._check_and_constrain_bounds(index_tracked, length, index_name)

    def _get_fixed_array_length(self, array_var: object) -> Optional[int]:
        """Get the length of a fixed-length array."""
        array_type = getattr(array_var, "type", None)
        if array_type is None:
            return None
        if not isinstance(array_type, ArrayType):
            return None
        if not array_type.is_fixed_array:
            return None
        if array_type.length_value is None:
            return None
        try:
            return int(str(array_type.length_value))
        except (ValueError, TypeError):
            return None

    def _get_or_create_index_var(
        self, index_value: object, domain: "IntervalDomain"
    ) -> Optional["TrackedSMTVariable"]:
        """Get or create tracked variable for index."""
        index_name = IntervalSMTUtils.resolve_variable_name(index_value)
        if index_name is None:
            return None

        tracked = IntervalSMTUtils.get_tracked_variable(domain, index_name)
        if tracked is not None:
            return tracked

        index_type = getattr(index_value, "type", None)
        index_elem_type = IntervalSMTUtils.resolve_elementary_type(index_type)
        if index_elem_type is None:
            return None

        tracked = IntervalSMTUtils.create_tracked_variable(
            self.solver, index_name, index_elem_type
        )
        if tracked is None:
            return None

        domain.state.set_range_variable(index_name, tracked)
        return tracked

    def _check_and_constrain_bounds(
        self, index_var: "TrackedSMTVariable", array_length: int, index_name: str
    ) -> None:
        """Check for OOB potential and add bounds constraint."""
        index_width = self.solver.bv_size(index_var.term)
        length_const = self.solver.create_constant(
            array_length, Sort(kind=SortKind.BITVEC, parameters=[index_width])
        )

        # Check if out-of-bounds is possible
        in_bounds = self.solver.bv_ult(index_var.term, length_const)
        out_of_bounds = self.solver.Not(in_bounds)

        self.solver.push()
        self.solver.assert_constraint(out_of_bounds)
        oob_possible = self.solver.check_sat() == CheckSatResult.SAT
        self.solver.pop()

        if oob_possible:
            self.logger.warning(
                "POTENTIAL OUT-OF-BOUNDS: '{index}' could be >= {length}",
                index=index_name,
                length=array_length,
            )

        # Add bounds constraint
        bounds_constraint = self.solver.bv_ult(index_var.term, length_const)
        self.solver.assert_constraint(bounds_constraint)

        self.logger.debug(
            "Added bounds constraint: '{index}' < {length}",
            index=index_name,
            length=array_length,
        )
