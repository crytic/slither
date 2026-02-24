"""Gasleft operation handler for interval analysis."""

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
from slither.slithir.operations.solidity_call import SolidityCall

if TYPE_CHECKING:
    from slither.analyses.data_flow.analyses.interval.analysis.domain import (
        IntervalDomain,
    )
    from slither.core.cfg.node import Node

GASLEFT_FUNCTIONS: frozenset[str] = frozenset({"gasleft()"})


class GasleftHandler(BaseOperationHandler):
    """Handler for gasleft() calls.

    gasleft() returns the remaining gas as uint256. Since the value
    is unknowable at static analysis time, the result is modeled as
    an unconstrained tracked variable.
    """

    def handle(
        self,
        operation: SolidityCall,
        domain: "IntervalDomain",
        node: "Node",
    ) -> None:
        """Process gasleft() operation."""
        if operation.lvalue is None:
            return

        lvalue = operation.lvalue
        if not isinstance(lvalue.type, ElementaryType):
            return

        result_name = get_variable_name(lvalue)
        sort = type_to_sort(lvalue.type)
        is_signed = is_signed_type(lvalue.type)
        bit_width = get_bit_width(lvalue.type)

        result_variable = TrackedSMTVariable.create(
            self.solver,
            result_name,
            sort,
            is_signed=is_signed,
            bit_width=bit_width,
        )
        domain.state.set_variable(result_name, result_variable)
