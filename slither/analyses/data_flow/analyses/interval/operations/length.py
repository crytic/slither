"""Length operation handler for interval analysis."""

from __future__ import annotations

from typing import TYPE_CHECKING

from slither.core.solidity_types.elementary_type import ElementaryType
from slither.slithir.operations.length import Length

from slither.analyses.data_flow.analyses.interval.operations.base import (
    BaseOperationHandler,
)
from slither.analyses.data_flow.analyses.interval.operations.type_utils import (
    get_variable_name,
    type_to_sort,
)
from slither.analyses.data_flow.analyses.interval.core.tracked_variable import (
    TrackedSMTVariable,
)

if TYPE_CHECKING:
    from slither.analyses.data_flow.analyses.interval.analysis.domain import (
        IntervalDomain,
    )
    from slither.core.cfg.node import Node


class LengthHandler(BaseOperationHandler):
    """Handler for Length operations (array/bytes length access)."""

    def handle(
        self,
        operation: Length,
        domain: "IntervalDomain",
        node: "Node",
    ) -> None:
        reference_name = get_variable_name(operation.lvalue)
        length_type = ElementaryType("uint256")
        sort = type_to_sort(length_type)

        tracked = TrackedSMTVariable.create(
            self.solver, reference_name, sort, is_signed=False, bit_width=256
        )
        domain.state.set_variable(reference_name, tracked)
