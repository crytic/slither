from typing import Union
from slither.analyses.data_flow.analyses.interval.analysis.domain import IntervalDomain
from slither.analyses.data_flow.analyses.interval.managers.variable_info_manager import (
    VariableInfoManager,
)
from slither.core.cfg.node import Node
from slither.slithir.operations.binary import Binary, BinaryType

from loguru import logger


class ComparisonHandler:

    def __init__(self):
        pass

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

        pass
