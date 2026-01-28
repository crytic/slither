"""Pytest configuration and fixtures for data flow analysis tests."""

import pytest
from pathlib import Path
from typing import Dict, Any, List

# Path to test contracts - relative to this file
# tests/conftest.py -> data_flow/ -> analyses/ -> slither/ -> slither/ -> contracts/src
CONTRACTS_DIR = Path(__file__).parent.parent.parent.parent.parent.parent / "contracts" / "src"

# List of contract files with expected results
TEST_CONTRACTS = [
    "Assert.sol",
    "Assignment.sol",
    "ByteExtractor.sol",
    "FunctionArgs.sol",
    "Length.sol",
    "Math.sol",
    "Member.sol",
    "Require.sol",
    "StateVariables.sol",
    "Timestamp.sol",
    "Unary.sol",
    "UnpackTest.sol",
]


@pytest.fixture
def contracts_dir() -> Path:
    """Return the path to test contracts directory."""
    return CONTRACTS_DIR


@pytest.fixture
def analyze_contract():
    """Fixture providing contract analysis function.

    Returns a function that analyzes a contract file and returns
    results as a dictionary suitable for snapshot comparison.
    """
    from slither.analyses.data_flow.test import analyze_contract_quiet

    def _analyze(contract_path: Path, timeout_ms: int = 1000) -> Dict[str, Any]:
        """Analyze a contract and return results as a dictionary."""
        results = analyze_contract_quiet(contract_path, timeout_ms=timeout_ms)

        output = {}
        for contract_result in results:
            contract_data = {}
            for func_name, func_result in sorted(contract_result.functions.items()):
                variables = {}
                for var_name, var_result in sorted(func_result.variables.items()):
                    variables[var_name] = {
                        "range": var_result.range_str,
                        "overflow": var_result.overflow,
                    }
                contract_data[func_name] = {"variables": variables}
            output[contract_result.contract_name] = contract_data
        return output

    return _analyze
