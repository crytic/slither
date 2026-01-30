"""Pytest configuration and fixtures for data flow analysis tests."""

import pytest
from pathlib import Path
from typing import Dict, Any

# Path to test contracts - relative to this file
# tests/conftest.py -> data_flow/ -> analyses/ -> slither/ -> slither/ -> contracts/src
CONTRACTS_DIR = Path(__file__).parent.parent.parent.parent.parent.parent / "contracts" / "src"

# List of contract files with expected results
TEST_CONTRACTS = [
    "Assert.sol",
    "Assignment.sol",
    "FunctionArgs.sol",
    "Length.sol",
    "Math.sol",
    "Member.sol",
    "Require.sol",
    "StateVariables.sol",
    "Timestamp.sol",
    "Unary.sol",
    "UnpackTest.sol",
    "SimpleIf.sol",
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
    from slither import Slither
    from slither.analyses.data_flow.run_analysis import (
        AnalysisConfig,
        _get_contracts,
        _analyze_contracts_json,
    )
    from slither.analyses.data_flow.smt_solver.cache import RangeQueryCache

    def _analyze(contract_path: Path, timeout_ms: int = 1000) -> Dict[str, Any]:
        """Analyze a contract and return results as a dictionary."""
        slither = Slither(str(contract_path))
        contracts = _get_contracts(slither)
        cache = RangeQueryCache(max_size=1000)
        config = AnalysisConfig(timeout_ms=timeout_ms)
        return _analyze_contracts_json(contracts, config, cache)

    return _analyze
