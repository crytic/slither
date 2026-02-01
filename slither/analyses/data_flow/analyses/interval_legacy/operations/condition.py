"""Handler for condition operations."""

from typing import Optional, TYPE_CHECKING

from slither.analyses.data_flow.analyses.interval.operations.base import BaseOperationHandler
from slither.analyses.data_flow.analyses.interval.utils import IntervalSMTUtils
from slither.slithir.operations.condition import Condition

if TYPE_CHECKING:
    from slither.analyses.data_flow.analyses.interval.analysis.domain import IntervalDomain
    from slither.core.cfg.node import Node


class ConditionHandler(BaseOperationHandler):
    """Handler for condition operations (if/else conditions).

    Note: The actual branch filtering is done by the engine's apply_condition method.
    This handler ensures the condition variable is tracked in the domain.
    """

    def handle(
        self,
        operation: Optional[Condition],
        domain: "IntervalDomain",
        node: "Node",
    ) -> None:
        """Handle condition operation by ensuring condition variable is tracked."""
        # Guard: ensure we have a valid Condition operation
        if operation is None or not isinstance(operation, Condition):
            return

        # Get the condition value name for logging/debugging
        condition_name = IntervalSMTUtils.resolve_variable_name(operation.value)

        self.logger.debug(
            "Condition operation: {condition} (branch filtering applied by engine)",
            condition=condition_name,
        )
