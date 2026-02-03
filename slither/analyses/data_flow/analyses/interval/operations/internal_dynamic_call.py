"""Internal dynamic call operation handler for interval analysis."""

from __future__ import annotations

from typing import TYPE_CHECKING, List

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
from slither.slithir.operations.internal_dynamic_call import InternalDynamicCall
from slither.slithir.variables.tuple import TupleVariable

if TYPE_CHECKING:
    from slither.analyses.data_flow.analyses.interval.analysis.domain import (
        IntervalDomain,
    )
    from slither.core.cfg.node import Node


class InternalDynamicCallHandler(BaseOperationHandler):
    """Handler for internal dynamic call operations.

    Internal dynamic calls are calls through function-type variables (function pointers).
    Since the target function is unknown at compile time, we create unconstrained
    results based on the function type's return signature.
    """

    def handle(
        self,
        operation: InternalDynamicCall,
        domain: "IntervalDomain",
        node: "Node",
    ) -> None:
        """Process internal dynamic call operation."""
        if operation.lvalue is None:
            return

        lvalue = operation.lvalue
        lvalue_type = lvalue.type

        if isinstance(lvalue, TupleVariable):
            self._handle_tuple_return(operation, domain)
            return

        if not isinstance(lvalue_type, ElementaryType):
            return

        result_name = get_variable_name(lvalue)
        self._create_unconstrained_result(result_name, lvalue_type, domain)

    def _handle_tuple_return(
        self,
        operation: InternalDynamicCall,
        domain: "IntervalDomain",
    ) -> None:
        """Handle dynamic calls that return tuples."""
        lvalue = operation.lvalue
        tuple_name = get_variable_name(lvalue)
        tuple_types = lvalue.type

        if not isinstance(tuple_types, list):
            return

        self._create_unconstrained_tuple(tuple_name, tuple_types, domain)

    def _create_unconstrained_tuple(
        self,
        tuple_name: str,
        tuple_types: List,
        domain: "IntervalDomain",
    ) -> None:
        """Create unconstrained variables for each tuple element."""
        for index, element_type in enumerate(tuple_types):
            if not isinstance(element_type, ElementaryType):
                continue
            element_name = f"{tuple_name}[{index}]"
            self._create_unconstrained_result(element_name, element_type, domain)

    def _create_unconstrained_result(
        self,
        name: str,
        element_type: ElementaryType,
        domain: "IntervalDomain",
    ) -> None:
        """Create an unconstrained variable for the result."""
        sort = type_to_sort(element_type)
        is_signed = is_signed_type(element_type)
        bit_width = get_bit_width(element_type)

        result_var = TrackedSMTVariable.create(
            self.solver, name, sort, is_signed=is_signed, bit_width=bit_width
        )
        domain.state.set_variable(name, result_var)
