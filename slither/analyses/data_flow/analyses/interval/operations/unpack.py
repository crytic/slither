"""Unpack operation handler for interval analysis."""

from __future__ import annotations

from typing import TYPE_CHECKING

from slither.analyses.data_flow.analyses.interval.core.tracked_variable import (
    TrackedSMTVariable,
)
from slither.analyses.data_flow.analyses.interval.operations.base import (
    BaseOperationHandler,
)
from slither.analyses.data_flow.analyses.interval.operations.type_utils import (
    get_bit_width,
    get_variable_name,
    is_signed_type,
    type_to_sort,
)
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.slithir.operations.unpack import Unpack

if TYPE_CHECKING:
    from slither.analyses.data_flow.analyses.interval.analysis.domain import (
        IntervalDomain,
    )
    from slither.core.cfg.node import Node


class UnpackHandler(BaseOperationHandler):
    """Handler for Unpack operations that extract tuple elements.

    Unpack operations extract individual elements from tuple variables,
    typically from function returns. Looks up the tuple element stored
    by InterproceduralHandler using the naming convention TUPLE_N[index].
    """

    def handle(
        self,
        operation: Unpack,
        domain: "IntervalDomain",
        node: "Node",
    ) -> None:
        """Process Unpack operation by extracting element from tracked tuple."""
        if operation.lvalue is None:
            return

        lvalue_type = operation.lvalue.type
        if not isinstance(lvalue_type, ElementaryType):
            return

        result_name = get_variable_name(operation.lvalue)
        tuple_name = get_variable_name(operation.tuple)
        element_index = operation.index

        # Look up the tuple element stored by InterproceduralHandler
        element_name = f"{tuple_name}[{element_index}]"
        tuple_element = domain.state.get_variable(element_name)

        sort = type_to_sort(lvalue_type)
        is_signed = is_signed_type(lvalue_type)
        bit_width = get_bit_width(lvalue_type)

        result_var = TrackedSMTVariable.create(
            self.solver, result_name, sort, is_signed=is_signed, bit_width=bit_width
        )

        # Constrain result to equal the tuple element if found
        if tuple_element is not None:
            self.solver.assert_constraint(result_var.term == tuple_element.term)

        domain.state.set_variable(result_name, result_var)
