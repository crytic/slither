from typing import Optional, Set, List
from slither.analyses.data_flow.interval_enhanced.analysis.domain import (
    IntervalDomain,
    DomainVariant,
)
from slither.analyses.data_flow.interval_enhanced.core.single_values import SingleValues
from slither.analyses.data_flow.interval_enhanced.managers.constraint_manager import (
    ConstraintManager,
)
from slither.core.cfg.node import Node, NodeType
from loguru import logger
from typing import TYPE_CHECKING
from decimal import Decimal

from slither.core.solidity_types.elementary_type import ElementaryType
from slither.slithir.operations.binary import Binary, BinaryType
from slither.slithir.variables.constant import Constant
from slither.analyses.data_flow.interval_enhanced.core.interval_range import IntervalRange
from slither.analyses.data_flow.interval_enhanced.core.state_info import StateInfo
from slither.analyses.data_flow.interval_enhanced.managers.variable_manager import VariableManager

if TYPE_CHECKING:
    from slither.analyses.data_flow.interval_enhanced.analysis.analysis import (
        IntervalAnalysisEnhanced,
    )


class IfHandler:
    def __init__(
        self,
        constraint_manager: ConstraintManager,
    ):
        self.constraint_manager = constraint_manager
        self.processed_nodes: Set[int] = set()
        self.variable_manager = VariableManager()
        self.inverse_domains: dict = {}  # Store inverse domains for later use
        self.if_operations: dict = {}  # Store if operations for later use

    def handle_if(
        self,
        node: Node,
        domain: IntervalDomain,
        operation: Binary,
        analysis_instance: "IntervalAnalysisEnhanced",
    ) -> None:
        print(
            f"🔄 HANDLING IF: {node.expression} at node {node.node_id} with operation {operation.type} and lvalue {operation.lvalue}"
        )

        # Store the inverse domain for later use
        inverse_domain = self.get_inverse_domain(node, operation, domain)
        self.inverse_domains[node.node_id] = inverse_domain
        self.if_operations[node.node_id] = operation

        # Apply the original if condition constraints
        self.constraint_manager.apply_constraint_from_variable(operation.lvalue, domain)

        return

    def handle_endif(self, node: Node, domain: IntervalDomain) -> None:
        """Retrieve stored inverse domain and merge it with current domain."""
        print(f"🔄 HANDLING ENDIF: {node.expression} at node {node.node_id}")

        # Find the corresponding if node for this endif
        if_node = self.find_matching_if_node(node)
        if not if_node:
            logger.error(f"Matching if node not found for endif node {node.node_id}")
            raise ValueError(f"Matching if node not found for endif node {node.node_id}")

        inverse_domain = self.inverse_domains[if_node.node_id]

        for var_name, inverse_state in inverse_domain.state.info.items():
            if var_name in domain.state.info:
                self._merge_if_else_states(domain.state.info[var_name], inverse_state)
            else:
                domain.state.info[var_name] = (
                    inverse_state.deep_copy()
                )  # uncoment this to bring out of scope variables into main domain

    def _merge_if_else_states(self, current_state: StateInfo, inverse_state: StateInfo) -> None:
        """Special merge for if-else scenarios that properly handles ranges and valid values."""

        # Join valid values
        current_state.valid_values = current_state.valid_values.join(inverse_state.valid_values)

        # Join invalid values
        current_state.invalid_values = current_state.invalid_values.join(
            inverse_state.invalid_values
        )

        # Remove any valid values that are also in invalid values
        for invalid_value in current_state.invalid_values:
            if invalid_value in inverse_state.invalid_values:
                current_state.valid_values.delete(invalid_value)

        # Start with the inverse ranges (else branch)
        result_ranges = [r.deep_copy() for r in inverse_state.interval_ranges]

        current_state.interval_ranges = result_ranges

    def find_matching_if_node(self, endif_node: Node) -> Node | None:
        """
        Find the corresponding IF node for a given ENDIF node.
        Uses immediate dominator first, then walks up dominators.
        """
        idom = endif_node.immediate_dominator
        if idom and idom.type == NodeType.IF:
            return idom

        # CFG approach -- might be better
        # visited = set()
        # queue = [endif_node.immediate_dominator] if endif_node.immediate_dominator else []

        # while queue:
        #     node = queue.pop(0)
        #     if node in visited:
        #         continue
        #     visited.add(node)

        #     if node.type == NodeType.IF:
        #         return node

        #     # Add the node's dominator (i.e., go up the tree)
        #     if node.immediate_dominator:
        #         queue.append(node.immediate_dominator)

        # return None

    def get_inverse_domain(
        self, node: Node, operation: Binary, current_domain: IntervalDomain
    ) -> IntervalDomain:
        """Compute the inverse domain for a given constraint."""
        print(
            f"🔄 GETTING INVERSE DOMAIN: {node.expression} at node {node.node_id} with operation {operation.type} and lvalue {operation.lvalue}"
        )

        # Create a copy of the current domain
        inverse_domain = current_domain.deep_copy()

        # Get the constraint details
        operator = operation.type
        left_operand = operation.variable_left
        right_operand = operation.variable_right

        # Clear the state for variables we're going to update to avoid contamination
        if inverse_domain.variant == DomainVariant.STATE:
            if hasattr(left_operand, "canonical_name"):
                original_var_name = self.variable_manager.get_variable_name(left_operand)
                if original_var_name in inverse_domain.state.info:
                    del inverse_domain.state.info[original_var_name]

            temp_var_name = self.variable_manager.get_variable_name(operation.lvalue)
            if temp_var_name in inverse_domain.state.info:
                del inverse_domain.state.info[temp_var_name]

        # Get the constant value from right operand
        if not isinstance(right_operand, Constant):
            logger.warning(f"Right operand is not a constant: {right_operand}")
            return inverse_domain

        constant_value = Decimal(str(right_operand.value))

        # Get type bounds for proper constraint application
        # Default to uint256 bounds
        type_min = Decimal("0")
        type_max = Decimal(
            "115792089237316195423570985008687907853269984665640564039457584007913129639935"
        )

        # Apply inverse constraint based on operator
        inverse_ranges = []

        if operator == BinaryType.GREATER:
            # x > 100 (inverse): x ≤ 100
            inverse_ranges.append(IntervalRange(lower_bound=type_min, upper_bound=constant_value))

        elif operator == BinaryType.GREATER_EQUAL:
            # x >= 100 (inverse): x < 100
            inverse_ranges.append(
                IntervalRange(lower_bound=type_min, upper_bound=constant_value - 1)
            )

        elif operator == BinaryType.LESS:
            # x < 100 (inverse): x ≥ 100
            inverse_ranges.append(IntervalRange(lower_bound=constant_value, upper_bound=type_max))

        elif operator == BinaryType.LESS_EQUAL:
            # x <= 100 (inverse): x > 100
            inverse_ranges.append(
                IntervalRange(lower_bound=constant_value + 1, upper_bound=type_max)
            )

        elif operator == BinaryType.EQUAL:
            # x == 100 (inverse): x ≠ 100
            # Create two ranges: [0, 99] and [101, max]
            if constant_value > type_min:
                inverse_ranges.append(
                    IntervalRange(lower_bound=type_min, upper_bound=constant_value - 1)
                )
            if constant_value < type_max:
                inverse_ranges.append(
                    IntervalRange(lower_bound=constant_value + 1, upper_bound=type_max)
                )

        elif operator == BinaryType.NOT_EQUAL:
            # x != 100 (inverse): x == 100
            # This creates a single value, so we'll handle it in the StateInfo creation
            inverse_ranges.append(
                IntervalRange(lower_bound=constant_value, upper_bound=constant_value)
            )

        else:
            logger.warning(f"Unknown comparison operator: {operator}")
            return inverse_domain

        # For equality conditions, the constant value becomes an invalid value in the inverse
        invalid_values = SingleValues()
        valid_values = SingleValues()

        if operator == BinaryType.EQUAL:
            invalid_values.add(constant_value)
        elif operator == BinaryType.NOT_EQUAL:
            # For != conditions, the constant value becomes a valid value in the inverse
            valid_values.add(constant_value)

        # Convert single-value ranges to valid values
        final_ranges = []
        for range_obj in inverse_ranges:
            if range_obj.get_lower() == range_obj.get_upper():
                # Single value range, convert to valid value
                valid_values.add(range_obj.get_lower())
            else:
                # Multi-value range, keep as range
                final_ranges.append(range_obj)

        inverse_state = StateInfo(
            interval_ranges=final_ranges,
            valid_values=valid_values,
            invalid_values=invalid_values,
            var_type=ElementaryType("uint256"),
        )

        # Find the target variable names and update their state info in the domain
        if inverse_domain.variant == DomainVariant.STATE:
            # Update the original variable (left operand) with inverse constraint
            # Only update if it's a proper variable (not a temporary)
            if hasattr(left_operand, "canonical_name"):
                original_var_name = self.variable_manager.get_variable_name(left_operand)
                inverse_domain.state.info[original_var_name] = inverse_state
                print(f"🔄 UPDATED ORIGINAL VARIABLE {original_var_name} with inverse constraint")

            # Update the temporary variable (lvalue) with inverse constraint
            temp_var_name = self.variable_manager.get_variable_name(operation.lvalue)
            inverse_domain.state.info[temp_var_name] = inverse_state
            print(f"🔄 UPDATED TEMP VARIABLE {temp_var_name} with inverse constraint")

        print(f"🔄 INVERSE DOMAIN: {[str(r) for r in inverse_ranges]}")
        return inverse_domain
