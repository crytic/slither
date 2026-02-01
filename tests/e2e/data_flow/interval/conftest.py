"""Pytest configuration and fixtures for data flow analysis tests."""

import pytest
from pathlib import Path
from typing import Dict, Any

# Path to test contracts - local contracts directory
CONTRACTS_DIR = Path(__file__).parent / "contracts"

# List of contract files with expected results
# Pending: Test_Add.sol, Test_Sub.sol, Test_Mul.sol require full Binary arithmetic
TEST_CONTRACTS = [
    "Test_Assignment.sol",
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
