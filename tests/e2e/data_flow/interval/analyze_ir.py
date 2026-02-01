#!/usr/bin/env python3
"""Analyze Solidity contracts and print IR operations.

Usage:
    python tests/e2e/data_flow/interval/analyze_ir.py <contract_path>
    python tests/e2e/data_flow/interval/analyze_ir.py tests/e2e/data_flow/interval/contracts/Test_Assignment.sol
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

from slither import Slither


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Analyze Solidity contracts with Slither")
    parser.add_argument("file_path", help="Path to the Solidity file to analyze")
    parser.add_argument(
        "--solc-version",
        default="0.8.19",
        help="Solidity compiler version (default: 0.8.19)",
    )
    parser.add_argument(
        "--evm-version",
        default="london",
        help="EVM version (default: london)",
    )
    parser.add_argument(
        "--skip-build",
        action="store_true",
        help="Skip Foundry build step",
    )
    return parser.parse_args()


def run_forge_build() -> None:
    """Run forge build if available."""
    print("Building with Foundry...")
    try:
        result = subprocess.run(
            ["forge", "build"],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        if result.returncode != 0:
            print(f"Warning: Foundry build failed: {result.stderr}")
            print("Continuing anyway...")
    except (FileNotFoundError, subprocess.TimeoutExpired) as error:
        print(f"Warning: Could not run forge build: {error}")
        print("Continuing anyway...")


def compile_contract(file_path: str, evm_version: str) -> Slither:
    """Compile contract with Slither."""
    print(f"Compiling directly with EVM {evm_version}...")
    try:
        return Slither(file_path, evm_version=evm_version, solc_disable_warnings=True)
    except Exception as error:
        print(f"Error: Could not compile: {error}")
        print("\nTrying with Foundry artifacts as fallback...")
        try:
            return Slither(file_path, solc_force_framework="foundry")
        except Exception as fallback_error:
            print(f"Error: Could not use Foundry framework either: {fallback_error}")
            sys.exit(1)


def print_function_info(function) -> None:
    """Print function entry point, parameters, and return values."""
    entry_node = function.entry_point
    if entry_node:
        print("\t\tEntry point:")
        print(f"\t\t\tNode ID: {entry_node.node_id}")
        if entry_node.expression:
            print(f"\t\t\tExpression: {entry_node.expression}")
        print(f"\t\t\tType: {entry_node.type}")

    if function.parameters:
        print("\t\tParameters:")
        for param in function.parameters:
            print(f"\t\t\t{param.name}: {param.type}")

    if function.return_values:
        print("\t\tReturn values:")
        for ret in function.return_values:
            print(f"\t\t\t{ret.name}: {ret.type}")


def print_ir_operations(function) -> None:
    """Print IR operations for each node."""
    for node in function.nodes:
        if node.expression:
            print(f"\t\t{node.expression}")
        else:
            print(f"\t\tNode {node.node_id}")
        for ir_op in node.irs_ssa:
            print(f"\t\t\t{ir_op}\t{type(ir_op).__name__}")


def main() -> None:
    """Main entry point."""
    args = parse_args()

    project_root = Path(__file__).parent.parent.parent.parent.parent
    os.chdir(project_root)

    if not args.skip_build:
        run_forge_build()

    slither = compile_contract(args.file_path, args.evm_version)

    for contract in slither.contracts:
        print(contract.name)
        for function in contract.functions:
            print(f"\t{function.name}")
            print_function_info(function)
            print_ir_operations(function)


if __name__ == "__main__":
    main()
