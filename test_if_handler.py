#!/usr/bin/env python3
"""
Test script to verify the IfHandler functionality with seen and unseen node handling.
"""

from slither import Slither
from slither.core.cfg.node import NodeType
from slither.analyses.data_flow.interval_enhanced.handlers.handle_if import IfHandler
from slither.analyses.data_flow.interval_enhanced.managers.constraint_manager import (
    ConstraintManager,
)
from slither.analyses.data_flow.interval_enhanced.analysis.domain import IntervalDomain


def test_if_handler():
    """Test the IfHandler with seen and unseen node handling"""

    # Create a Solidity contract with if-else if-else structure
    contract_code = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract TestContract {
    uint256 public value;
    
    function testIfElseIfElse(uint256 x) public {
        if (x == 4) {
            value = 10;
        } else if (x == 5) {
            value = 20;
        } else {
            value = 30;
        }
    }
}
"""

    # Write the contract to a temporary file
    with open("test_contract.sol", "w") as f:
        f.write(contract_code)

    try:
        # Parse the contract
        slither = Slither("test_contract.sol")
        contract = slither.contracts[0]

        # Get the function
        test_func = contract.get_function_from_signature("testIfElseIfElse(uint256)")

        # Create the IfHandler
        constraint_manager = ConstraintManager()
        if_handler = IfHandler(constraint_manager)

        print("Testing IfHandler with seen and unseen node handling:")
        print("=" * 70)

        # Find all IF nodes
        if_nodes = [node for node in test_func.nodes if node.type == NodeType.IF]
        print(f"Found {len(if_nodes)} IF nodes")

        # Create a dummy domain for testing
        domain = IntervalDomain.with_state({})

        print(f"\n{'='*20} FIRST CALL (UNSEEN NODES) {'='*20}")
        # First call - should build branch structure
        for i, if_node in enumerate(if_nodes):
            print(f"\n--- Processing IF node {i+1}: {if_node.node_id} ---")
            if_handler.handle_if(if_node, domain)

        print(f"\n{'='*20} SECOND CALL (SEEN NODES) {'='*20}")
        # Second call - should print branch info
        for i, if_node in enumerate(if_nodes):
            print(f"\n--- Processing IF node {i+1}: {if_node.node_id} ---")
            if_handler.handle_if(if_node, domain)

        print(f"\n{'='*20} BRANCH POINTS SUMMARY {'='*20}")
        all_branch_points = if_handler.get_all_branch_points()
        print(f"Total branch points found: {len(all_branch_points)}")

        for i, bp in enumerate(all_branch_points):
            print(f"\nBranch point {i+1}:")
            print(f"  Node ID: {bp.node_id}")
            print(f"  Type: {bp.branch_type}")
            print(f"  Condition: {bp.condition_expression}")
            print(f"  True branch: {bp.true_branch_node}")
            print(f"  False branch: {bp.false_branch_node}")

        print(f"\n{'='*20} CHAIN SUMMARY {'='*20}")
        for root_id, chain_nodes in if_handler.if_chains.items():
            print(f"Chain starting at node {root_id}: {chain_nodes}")

        print("\n" + "=" * 70)
        print("Test completed!")

    except Exception as e:
        print(f"Error during test: {e}")
        import traceback

        traceback.print_exc()

    finally:
        # Clean up
        import os

        if os.path.exists("test_contract.sol"):
            os.remove("test_contract.sol")


if __name__ == "__main__":
    test_if_handler()
