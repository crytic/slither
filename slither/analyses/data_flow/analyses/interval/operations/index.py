"""Index operation handler for interval analysis."""

from __future__ import annotations

from typing import TYPE_CHECKING

from slither.core.solidity_types.elementary_type import ElementaryType
from slither.core.variables.variable import Variable
from slither.slithir.operations.index import Index
from slither.slithir.variables.constant import Constant

from slither.analyses.data_flow.analyses.interval.operations.base import (
    BaseOperationHandler,
)
from slither.analyses.data_flow.analyses.interval.operations.type_utils import (
    get_variable_name,
    get_bit_width,
    is_signed_type,
    type_to_sort,
)
from slither.analyses.data_flow.analyses.interval.operations.type_conversion import (
    match_width,
)
from slither.analyses.data_flow.analyses.interval.core.tracked_variable import (
    TrackedSMTVariable,
)

if TYPE_CHECKING:
    from slither.analyses.data_flow.analyses.interval.analysis.domain import (
        IntervalDomain,
    )
    from slither.core.cfg.node import Node


class IndexHandler(BaseOperationHandler):
    """Handler for Index operations (array element access)."""

    def handle(
        self,
        operation: Index,
        domain: "IntervalDomain",
        node: "Node",
    ) -> None:
        element_type = self._get_element_type(operation)
        if element_type is None:
            return

        reference_name = get_variable_name(operation.lvalue)
        element_name = self._build_element_name(operation)

        tracked_reference = self._create_reference_variable(
            reference_name, element_type, domain
        )
        self._link_reference_to_element(
            tracked_reference, element_name, element_type, domain
        )

    def _get_element_type(self, operation: Index) -> ElementaryType | None:
        lvalue_type = operation.lvalue.type
        if isinstance(lvalue_type, ElementaryType):
            return lvalue_type
        return None

    def _build_element_name(self, operation: Index) -> str:
        """Build element name using points_to for write-through semantics."""
        points_to_target = operation.lvalue.points_to
        if isinstance(points_to_target, Variable):
            array_name = get_variable_name(points_to_target)
        else:
            array_name = get_variable_name(operation.variable_left)

        index_value = operation.variable_right

        if isinstance(index_value, Constant):
            index_string = str(index_value.value)
        else:
            index_string = get_variable_name(index_value)

        return f"{array_name}[{index_string}]"

    def _create_reference_variable(
        self,
        reference_name: str,
        element_type: ElementaryType,
        domain: "IntervalDomain",
    ) -> TrackedSMTVariable:
        sort = type_to_sort(element_type)
        signed = is_signed_type(element_type)
        bit_width = get_bit_width(element_type)

        tracked = TrackedSMTVariable.create(
            self.solver, reference_name, sort, is_signed=signed, bit_width=bit_width
        )
        domain.state.set_variable(reference_name, tracked)
        return tracked

    def _link_reference_to_element(
        self,
        tracked_reference: TrackedSMTVariable,
        element_name: str,
        element_type: ElementaryType,
        domain: "IntervalDomain",
    ) -> None:
        tracked_element = domain.state.get_variable(element_name)

        if tracked_element is None:
            tracked_element = self._create_element_variable(
                element_name, element_type, domain
            )

        element_term = match_width(
            self.solver, tracked_element.term, tracked_reference.term
        )
        self.solver.assert_constraint(tracked_reference.term == element_term)

    def _create_element_variable(
        self,
        element_name: str,
        element_type: ElementaryType,
        domain: "IntervalDomain",
    ) -> TrackedSMTVariable:
        sort = type_to_sort(element_type)
        signed = is_signed_type(element_type)
        bit_width = get_bit_width(element_type)

        tracked = TrackedSMTVariable.create(
            self.solver, element_name, sort, is_signed=signed, bit_width=bit_width
        )
        domain.state.set_variable(element_name, tracked)
        return tracked
