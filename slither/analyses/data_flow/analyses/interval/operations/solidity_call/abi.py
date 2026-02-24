"""ABI encoding/decoding operation handlers for interval analysis."""

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
from slither.slithir.operations.solidity_call import SolidityCall
from slither.slithir.variables.tuple import TupleVariable

if TYPE_CHECKING:
    from slither.analyses.data_flow.analyses.interval.analysis.domain import (
        IntervalDomain,
    )
    from slither.core.cfg.node import Node

ABI_FUNCTIONS: frozenset[str] = frozenset({
    "abi.decode()",
    "abi.encode()",
    "abi.encodePacked()",
    "abi.encodeWithSelector()",
    "abi.encodeWithSignature()",
    "abi.encodeCall()",
})


class AbiHandler(BaseOperationHandler):
    """Handler for ABI encoding and decoding operations.

    ABI decode unpacks arbitrary bytes into typed values, so the
    results are unconstrained. ABI encode variants produce opaque
    bytes, equally unconstrained from the analysis perspective.
    """

    def handle(
        self,
        operation: SolidityCall,
        domain: "IntervalDomain",
        node: "Node",
    ) -> None:
        """Process ABI encode/decode operation."""
        if operation.lvalue is None:
            return

        lvalue = operation.lvalue

        if isinstance(lvalue, TupleVariable):
            self._handle_tuple_return(operation, domain)
            return

        if not isinstance(lvalue.type, ElementaryType):
            return

        result_name = get_variable_name(lvalue)
        self._create_unconstrained_result(
            result_name, lvalue.type, domain
        )

    def _handle_tuple_return(
        self,
        operation: SolidityCall,
        domain: "IntervalDomain",
    ) -> None:
        """Handle ABI calls that return tuples."""
        lvalue = operation.lvalue
        tuple_name = get_variable_name(lvalue)
        tuple_types = lvalue.type

        if not isinstance(tuple_types, list):
            return

        self._create_unconstrained_tuple(
            tuple_name, tuple_types, domain
        )

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
            self._create_unconstrained_result(
                element_name, element_type, domain
            )

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

        result_variable = TrackedSMTVariable.create(
            self.solver,
            name,
            sort,
            is_signed=is_signed,
            bit_width=bit_width,
        )
        domain.state.set_variable(name, result_variable)
