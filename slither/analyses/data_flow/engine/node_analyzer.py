from typing import Optional

from slither.core.cfg.node import Node, NodeType
from slither.slithir.operations.binary import Binary, BinaryType


class NodeAnalyzer:
    """Utility class for analyzing CFG nodes and extracting conditions."""

    @staticmethod
    def extract_condition(node: Node) -> Optional[Binary]:
        """Extract comparison condition from IF or IFLOOP node."""
        if node.type not in [NodeType.IF, NodeType.IFLOOP]:
            return None

        # Look for the last binary operation (comparison or boolean)
        last_binary_op = None
        for operation in node.irs or []:
            if isinstance(operation, Binary) and operation.type in [
                BinaryType.GREATER,
                BinaryType.GREATER_EQUAL,
                BinaryType.LESS,
                BinaryType.LESS_EQUAL,
                BinaryType.EQUAL,
                BinaryType.NOT_EQUAL,
                BinaryType.ANDAND,  # Added for compound boolean operations
                BinaryType.OROR,    # Added for compound boolean operations
            ]:
                last_binary_op = operation  # Return LAST, not FIRST
        return last_binary_op

    @staticmethod
    def is_conditional_node(node: Node) -> bool:
        """Check if node represents a conditional branch."""
        return node.type in [NodeType.IF, NodeType.IFLOOP] and len(node.sons) >= 2
