from slither.analyses.data_flow.interval_enhanced.analysis.domain import IntervalDomain
from slither.analyses.data_flow.interval_enhanced.managers.constraint_manager import (
    ConstraintManager,
)
from slither.analyses.data_flow.interval_enhanced.managers.branch_manager import (
    BranchManager,
    BranchSplit,
)
from slither.core.cfg.node import Node
from loguru import logger


class IfHandler:
    def __init__(self, constraint_manager: ConstraintManager, branch_manager: BranchManager):
        self.constraint_manager = constraint_manager
        self.branch_manager = branch_manager
        self.processed_nodes: set = set()  # Track nodes that have already been processed

    def handle_if(self, node: Node, domain: IntervalDomain) -> BranchSplit:
        """Handle if node - create two domain copies for basic splitting"""
        # Check if this node has already been processed
        if node.node_id in self.processed_nodes:
            logger.debug(f"⏭️  Skipping already processed IF node: {node.node_id}")
            # Return existing branch split or create a minimal one
            return self.branch_manager.get_existing_branch_split(node.node_id)

        logger.debug(f"🔄 Splitting domain at IF node: {node.node_id}")
        domain_info = {k: str(v) for k, v in domain.state.info.items()}
        logger.debug(f"📊 Domain state before splitting: {domain_info}")

        # Create branch domains using BranchManager
        branch_split = self.branch_manager.create_branch_domains(domain, node.node_id)

        # Mark this node as processed
        self.processed_nodes.add(node.node_id)

        logger.debug(f"✅ Created true branch domain: {branch_split.true_branch_id}")
        logger.debug(f"✅ Created false branch domain: {branch_split.false_branch_id}")

        # Log the domain states (should be identical at this stage)
        true_info = {k: str(v) for k, v in branch_split.true_domain.state.info.items()}
        false_info = {k: str(v) for k, v in branch_split.false_domain.state.info.items()}
        logger.debug(f"📈 True branch domain: {true_info}")
        logger.debug(f"📉 False branch domain: {false_info}")

        return branch_split
