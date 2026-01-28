"""Pytest tests for interval analysis using snapshot testing.

Run tests:
    pytest slither/analyses/data_flow/tests/ -v

Update snapshots:
    pytest slither/analyses/data_flow/tests/ --snapshot-update

Run single contract:
    pytest -k "Assert.sol" -v
"""

import pytest
from pathlib import Path

from .conftest import TEST_CONTRACTS


class TestIntervalAnalysis:
    """Test suite for interval analysis results using snapshots."""

    @pytest.mark.parametrize("contract_file", TEST_CONTRACTS)
    def test_contract_analysis(
        self,
        contract_file: str,
        analyze_contract,
        snapshot,
        contracts_dir: Path,
    ):
        """Test interval analysis for a contract file.

        Analyzes the contract and compares results against stored snapshots.
        To update snapshots after changes: pytest --snapshot-update
        """
        contract_path = contracts_dir / contract_file

        if not contract_path.exists():
            pytest.skip(f"Contract not found: {contract_path}")

        results = analyze_contract(contract_path)
        assert results == snapshot
