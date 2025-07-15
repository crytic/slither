from typing import Dict
from slither.analyses.data_flow.interval_enhanced.analysis.domain import IntervalDomain


class BranchSplit:
    """Represents the result of splitting a domain into true/false branches."""

    def __init__(
        self,
        true_domain: IntervalDomain,
        false_domain: IntervalDomain,
        true_branch_id: str,
        false_branch_id: str,
    ):
        self.true_domain = true_domain
        self.false_domain = false_domain
        self.true_branch_id = true_branch_id
        self.false_branch_id = false_branch_id


class BranchManager:
    """Central component to manage domain splitting for if-else branches."""

    def __init__(self):
        # Store active branch domains: branch_id -> IntervalDomain
        self.active_branches: Dict[str, IntervalDomain] = {}

        # Counter for generating unique branch IDs
        self._branch_counter = 0

    def create_branch_domains(
        self, original_domain: IntervalDomain, if_node_id: int
    ) -> BranchSplit:
        """Create true and false branch domains from original domain."""
        # Create two copies of the domain
        true_domain = original_domain.deep_copy()
        false_domain = original_domain.deep_copy()

        # Generate unique branch IDs
        true_branch_id = f"if_{if_node_id}_true"
        false_branch_id = f"if_{if_node_id}_false"

        # Store in active branches
        self.active_branches[true_branch_id] = true_domain
        self.active_branches[false_branch_id] = false_domain

        return BranchSplit(true_domain, false_domain, true_branch_id, false_branch_id)

    def get_branch_domain(self, branch_id: str) -> IntervalDomain:
        """Get domain for a specific branch."""
        return self.active_branches.get(branch_id)

    def is_branch_active(self, branch_id: str) -> bool:
        """Check if branch is active."""
        return branch_id in self.active_branches

    def get_existing_branch_split(self, if_node_id: int) -> BranchSplit:
        """Get existing branch split for a node that has already been processed."""
        true_branch_id = f"if_{if_node_id}_true"
        false_branch_id = f"if_{if_node_id}_false"

        # Get existing domains or create empty ones if not found
        true_domain = self.active_branches.get(true_branch_id, IntervalDomain.with_state({}))
        false_domain = self.active_branches.get(false_branch_id, IntervalDomain.with_state({}))

        return BranchSplit(true_domain, false_domain, true_branch_id, false_branch_id)
