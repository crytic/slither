"""InitArray operation handler for interval analysis."""

from __future__ import annotations

from typing import TYPE_CHECKING

from slither.core.solidity_types.array_type import ArrayType
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.slithir.operations.init_array import InitArray

from slither.analyses.data_flow.analyses.interval.operations.base import (
    BaseOperationHandler,
)
from slither.analyses.data_flow.analyses.interval.operations.type_utils import (
    get_variable_name,
    get_bit_width,
    is_signed_type,
    type_to_sort,
    constrain_to_value,
)
from slither.analyses.data_flow.analyses.interval.core.tracked_variable import (
    TrackedSMTVariable,
)

if TYPE_CHECKING:
    from slither.analyses.data_flow.analyses.interval.analysis.domain import (
        IntervalDomain,
    )
    from slither.core.cfg.node import Node


class InitArrayHandler(BaseOperationHandler):
    """Handler for InitArray operations (array literal initialization)."""

    def handle(
        self,
        operation: InitArray,
        domain: "IntervalDomain",
        node: "Node",
    ) -> None:
        element_type = self._get_element_type(operation)
        if element_type is None:
            return

        lvalue_name = get_variable_name(operation.lvalue)

        for index, init_value in enumerate(operation.init_values):
            if isinstance(init_value, list):
                continue
            self._process_element(
                lvalue_name, index, init_value, element_type, domain
            )

    def _get_element_type(
        self, operation: InitArray
    ) -> ElementaryType | None:
        lvalue_type = operation.lvalue.type
        if not isinstance(lvalue_type, ArrayType):
            return None
        if not isinstance(lvalue_type.type, ElementaryType):
            return None
        return lvalue_type.type

    def _process_element(
        self,
        array_name: str,
        index: int,
        init_value: object,
        element_type: ElementaryType,
        domain: "IntervalDomain",
    ) -> None:
        element_name = f"{array_name}[{index}]"
        sort = type_to_sort(element_type)
        signed = is_signed_type(element_type)
        bit_width = get_bit_width(element_type)

        tracked = TrackedSMTVariable.create(
            self.solver,
            element_name,
            sort,
            is_signed=signed,
            bit_width=bit_width,
        )
        domain.state.set_variable(element_name, tracked)
        constrain_to_value(self.solver, tracked, init_value, domain)
