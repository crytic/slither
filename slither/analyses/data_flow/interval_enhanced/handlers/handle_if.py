from typing import Set, Dict, List, Tuple

from slither.analyses.data_flow.interval_enhanced.analysis.domain import IntervalDomain
from slither.analyses.data_flow.interval_enhanced.managers.constraint_manager import (
    ConstraintManager,
)
from slither.core.cfg.node import Node, NodeType
from slither.slithir.operations import Condition
from loguru import logger


class BranchPoint:
    """Represents a point where the domain needs to be split"""

    def __init__(
        self,
        node_id: int,
        condition: Condition,
        true_branch_node: int,
        false_branch_node: int,
        branch_type: str,
    ):
        self.node_id = node_id
        self.condition = condition
        self.true_branch_node = true_branch_node
        self.false_branch_node = false_branch_node
        self.branch_type = branch_type  # "if", "else_if"


class IfHandler:
    def __init__(self, constraint_manager: ConstraintManager):
        self.constraint_manager = constraint_manager
        self.seen_if_nodes: Set[int] = set()
        self.branch_points: Dict[int, BranchPoint] = {}  # node_id -> BranchPoint
        self.if_chains: Dict[int, List[int]] = {}  # root_node_id -> [all nodes in chain]

    def handle_if(self, node: Node, domain: IntervalDomain) -> None:
        """Handle if node - find all branching points in the if-else-if-else chain"""
        if node.node_id in self.seen_if_nodes:
            self.handle_seen_if_node(node, domain)
        else:
            self.handle_unseen_if_node(node, domain)

    def handle_unseen_if_node(self, node: Node, domain: IntervalDomain) -> None:
        """Handle an unseen IF node by building the branch structure"""
        logger.debug(f"Building branch structure for unseen IF node: {node.node_id}")

        # Find all branching points in this chain
        branch_points, chain_nodes = self.find_all_branch_points(node)

        # Store the results
        self.if_chains[node.node_id] = chain_nodes
        for branch_point in branch_points:
            self.branch_points[branch_point.node_id] = branch_point
            self.seen_if_nodes.add(branch_point.node_id)

        # logger.debug(f"Built branch structure with {len(branch_points)} branch points")

    def handle_seen_if_node(self, node: Node, domain: IntervalDomain) -> None:
        """Handle a seen IF node by determining which branch it belongs to"""
        logger.debug(f"Processing seen IF node: {node.node_id}")
        self.print_branch_info(node)

    def print_branch_info(self, node: Node) -> None:
        """Print information about which branch this node belongs to"""
        if not self.is_branch_point(node.node_id):
            logger.debug(f"Node {node.node_id} is not a branch point")
            return

        branch_point = self.get_branch_point(node.node_id)
        logger.debug(f"Node {node.node_id} belongs to {branch_point.branch_type} branch")

        if branch_point.condition:
            logger.debug(f"  If-true condition: {branch_point.condition.expression}")
            logger.debug(f"  Condition variable: {branch_point.condition.value}")
        else:
            logger.debug(f"  No condition found")

    def find_all_branch_points(self, start_node: Node) -> Tuple[List[BranchPoint], List[int]]:
        """Find all nodes that create branches (IF, ELSE IF) in the chain"""
        branch_points = []
        all_nodes = []
        current_node = start_node
        is_first = True

        while current_node and current_node.type == NodeType.IF:
            # Find the Condition operation in the node's IRs
            condition_op = None
            for ir in current_node.irs:
                if isinstance(ir, Condition):
                    condition_op = ir
                    break

            # This is a branching point - domain needs to be split here
            branch_point = BranchPoint(
                node_id=current_node.node_id,
                condition=condition_op,
                true_branch_node=current_node.son_true.node_id if current_node.son_true else None,
                false_branch_node=(
                    current_node.son_false.node_id if current_node.son_false else None
                ),
                branch_type="if" if is_first else "else_if",
            )

            branch_points.append(branch_point)
            all_nodes.append(current_node.node_id)

            logger.debug(
                f"Found branch point: {branch_point.branch_type} at node {current_node.node_id}"
            )

            # Move to the next node in the chain (false branch)
            current_node = current_node.son_false
            is_first = False

            # If the false branch is not another IF, we've reached the else or end
            if current_node and current_node.type != NodeType.IF:
                all_nodes.append(current_node.node_id)
                logger.debug(f"Found else/end node: {current_node.node_id}")
                break

        return branch_points, all_nodes

    def is_branch_point(self, node_id: int) -> bool:
        """Check if this node is a branching point where domain should be split"""
        return node_id in self.branch_points

    def get_branch_point(self, node_id: int) -> BranchPoint:
        """Get the branch point information for a node"""
        return self.branch_points.get(node_id)
