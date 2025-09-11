from slither.analyses.data_flow.analyses.interval.analysis.domain import IntervalDomain
from slither.analyses.data_flow.analyses.interval.managers.constraint_manager import (
    ComparisonConstraintStorage,
)
from slither.core.cfg.node import Node
from slither.slithir.operations.binary import Binary, BinaryType

from loguru import logger


class ComparisonHandler:
    """Handler for comparison operations in interval analysis."""

    def __init__(self):
        # Initialize storage for comparison constraints
        self.constraint_storage = ComparisonConstraintStorage()

    def handle_comparison(self, node: Node, domain: IntervalDomain, operation: Binary):
        # Check if this is a valid comparison operation
        valid_comparison_types = {
            BinaryType.GREATER,
            BinaryType.LESS,
            BinaryType.GREATER_EQUAL,
            BinaryType.LESS_EQUAL,
            BinaryType.EQUAL,
            BinaryType.NOT_EQUAL,
        }

        if operation.type not in valid_comparison_types:
            logger.error("Comparison operation type is not a valid comparison type")
            raise ValueError("Comparison operation type is not a valid comparison type")

        # Store the comparison operation constraint for future use
        self.constraint_storage.store_comparison_operation_constraint(operation, domain)

        logger.debug(f"Stored comparison operation: {operation.type} at node {node}")
