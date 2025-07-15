from typing import Set
from slither.analyses.data_flow.interval_enhanced.analysis.domain import IntervalDomain
from slither.analyses.data_flow.interval_enhanced.managers.constraint_manager import (
    ConstraintManager,
)
from slither.analyses.data_flow.interval_enhanced.managers.branch_manager import (
    BranchManager,
    BranchSplit,
)
from slither.core.cfg.node import Node, NodeType
from loguru import logger
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from slither.analyses.data_flow.interval_enhanced.analysis.analysis import (
        IntervalAnalysisEnhanced,
    )


class IfHandler:
    def __init__(self, constraint_manager: ConstraintManager, branch_manager: BranchManager):
        self.constraint_manager = constraint_manager
        self.branch_manager = branch_manager
        self.processed_nodes: Set[int] = set()

    def handle_if(
        self, node: Node, domain: IntervalDomain, analysis_instance: "IntervalAnalysisEnhanced"
    ) -> None:
        """Handle if node - create two domain copies and traverse to branches"""

        if node.node_id in self.processed_nodes:
            return

        # Check if this is the final chain (FALSE branch is None/empty)
        is_final_chain = (
            node.son_false is None
            or node.son_false.expression is None
            or str(node.son_false.expression) == "None"
        )

        if is_final_chain:
            logger.debug(f"📍 CHAIN END: {node.expression} - only TRUE branch")

            # Create branch domains but only use TRUE branch
            branch_split = self.branch_manager.create_branch_domains(domain, node.node_id)
            self.processed_nodes.add(node.node_id)

            # Only process TRUE branch - it inherits the current domain
            if node.son_true:
                logger.debug(f"🔄 BRANCH START: TRUE branch from chain end")
                self._process_branch_node(
                    node.son_true, branch_split.true_domain, analysis_instance, "TRUE"
                )
                logger.debug(f"✅ BRANCH END: TRUE branch from chain end")

            return

        # Normal processing - both branches
        logger.debug(f"🔄 BRANCH SPLIT: {node.expression}")

        branch_split = self.branch_manager.create_branch_domains(domain, node.node_id)
        self.processed_nodes.add(node.node_id)

        try:
            # Process TRUE branch
            if node.son_true:
                logger.debug(f"🔄 BRANCH START: TRUE branch")
                self._process_branch_node(
                    node.son_true, branch_split.true_domain, analysis_instance, "TRUE"
                )
                logger.debug(f"✅ BRANCH END: TRUE branch")

            # Process FALSE branch
            if node.son_false:
                logger.debug(f"🔄 BRANCH START: FALSE branch")
                self._process_branch_node(
                    node.son_false, branch_split.false_domain, analysis_instance, "FALSE"
                )
                logger.debug(f"✅ BRANCH END: FALSE branch")

        except Exception as e:
            logger.error(f"❌ Error during branch processing: {e}")
            raise

    def _process_branch_node(
        self,
        branch_node: Node,
        branch_domain: IntervalDomain,
        analysis_instance: "IntervalAnalysisEnhanced",
        branch_type: str,
    ) -> None:
        """Process a single branch node with minimal logging"""

        # Handle IF nodes specially
        if branch_node.type == NodeType.IF:
            if branch_node.node_id in self.processed_nodes:
                return
            else:
                if branch_type == "FALSE":
                    # This is an else-if continuation
                    logger.debug(f"🔗 ELSE-IF CONTINUATION: {branch_node.expression}")
                    self.handle_if(branch_node, branch_domain, analysis_instance)
                    return
                else:
                    # Nested IF - not supported
                    logger.error(f"❌ NESTED IF: {branch_node.expression} - Not supported")
                    raise NotImplementedError(f"Nested IF not supported: {branch_node.expression}")

        # Process IRs
        for ir in branch_node.irs:
            analysis_instance.transfer_function_helper(branch_node, branch_domain, ir, [])

        # Continue to next nodes
        for son in branch_node.sons:
            self._process_branch_node(son, branch_domain, analysis_instance, branch_type)
