from typing import List
from slither.core.cfg.node import Node
from slither.slithir.operations.solidity_call import SolidityCall
from slither.analyses.data_flow.analyses.interval.analysis.domain import IntervalDomain
from slither.analyses.data_flow.analyses.interval.managers.constraint_manager import (
    ComparisonConstraintStorage,
)

from loguru import logger


class SolidityCallHandler:
    """Handler for Solidity call operations, specifically require/assert functions."""

    def __init__(self, constraint_storage: ComparisonConstraintStorage = None):
        # Use provided constraint storage or create a new one
        if constraint_storage is not None:
            self.constraint_storage = constraint_storage
        else:
            self.constraint_storage = ComparisonConstraintStorage()

    def handle_solidity_call(
        self, node: Node, domain: IntervalDomain, operation: SolidityCall
    ) -> None:
        """Handle require/assert functions by storing constraints"""
        require_assert_functions: List[str] = [
            "require(bool)",
            "assert(bool)",
            "require(bool,string)",
            "require(bool,error)",
        ]

        # Only process require/assert functions
        if operation.function.name not in require_assert_functions:
            logger.error(
                f"Operation function name is not a require/assert function: {operation.function.name}"
            )
            raise ValueError(
                f"Operation function name is not a require/assert function: {operation.function.name}"
            )

        if not operation.arguments:
            logger.error("Operation arguments are empty")
            raise ValueError("Operation arguments are empty")

        condition_variable = operation.arguments[0]

        self.constraint_storage.apply_constraint_from_variable(condition_variable, domain)
        logger.debug(
            f"Require/assert function encountered: {operation.function.name} with condition: {condition_variable}"
        )
