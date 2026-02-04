"""Pytest tests for rounding analysis using snapshot testing.

Run tests:
    pytest tests/e2e/data_flow/rounding/ -v

Update snapshots:
    pytest tests/e2e/data_flow/rounding/ --snapshot-update

Run single contract:
    pytest -k "Assignment" -v
"""

import json
import pytest
from pathlib import Path

from .conftest import TEST_CONTRACTS


class TestRoundingAnalysis:
    """Test suite for rounding analysis results using snapshots."""

    @pytest.mark.parametrize("contract_file", TEST_CONTRACTS)
    def test_contract_analysis(
        self,
        contract_file: str,
        analyze_contract,
        snapshot,
        contracts_dir: Path,
    ):
        """Test rounding analysis for a contract file.

        Analyzes the contract and compares results against stored snapshots.
        To update snapshots after changes: pytest --snapshot-update
        """
        contract_path = contracts_dir / contract_file

        if not contract_path.exists():
            pytest.skip(f"Contract not found: {contract_path}")

        results = analyze_contract(contract_path)
        # Convert to JSON string for snapshot comparison
        results_json = json.dumps(results, indent=2, sort_keys=True)
        snapshot.assert_match(results_json, f"{contract_file}.json")
