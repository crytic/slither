"""Tests for BlockNumberDuration detector and Constant.subdenomination."""

import tempfile
from pathlib import Path
from slither import Slither
from slither.detectors.operations.block_number_duration import (
    BlockNumberDuration,
    _detect_block_number_duration,
)
from slither.slithir.variables.constant import Constant


def test_constant_subdenomination_property():
    c1 = Constant("1", subdenomination="days")
    assert c1.subdenomination == "days"
    assert c1.value == 86400
    assert c1.original_value == "1"

    c2 = Constant("10", subdenomination=None)
    assert c2.subdenomination is None
    assert c2.value == 10


def test_block_number_duration_detection():
    code = """
    // SPDX-License-Identifier: MIT
    pragma solidity ^0.8.20;

    contract TestContract {
        uint256 public constant CLIFF = 7 days;
        uint256 public constant LARGE_BLOCKS = 2628000;

        function badDirect(uint256 start) external view returns (bool) {
            return block.number > start + 1 days;
        }

        function badConstant(uint256 start) external view returns (bool) {
            return block.number > start + CLIFF;
        }

        function badLargeBlocks(uint256 start) external view returns (bool) {
            return block.number > start + LARGE_BLOCKS;
        }

        function badDirectAdd() external view returns (uint256) {
            return block.number + 3 days;
        }

        function goodTimestamp(uint256 start) external view returns (bool) {
            return block.timestamp > start + 1 days;
        }

        function goodSmallBlocks(uint256 start) external view returns (bool) {
            return block.number > start + 10;
        }
    }
    """

    with tempfile.NamedTemporaryFile("w", suffix=".sol", delete=False) as f:
        f.write(code)
        sol_path = f.name

    try:
        sl = Slither(sol_path)
        contract = sl.get_contract_from_name("TestContract")[0]
        findings = _detect_block_number_duration(contract)

        detected_funcs = {func.name for func, _ in findings}

        # Verify all buggy functions are detected
        assert "badDirect" in detected_funcs
        assert "badConstant" in detected_funcs
        assert "badLargeBlocks" in detected_funcs
        assert "badDirectAdd" in detected_funcs

        # Verify benign functions are NOT detected (0 false positives)
        assert "goodTimestamp" not in detected_funcs
        assert "goodSmallBlocks" not in detected_funcs

        # Verify detector Output generation
        import logging

        detector = BlockNumberDuration(sl.compilation_units[0], sl, logging.getLogger("test"))
        outputs = detector._detect()
        assert len(outputs) == 4
    finally:
        Path(sol_path).unlink(missing_ok=True)
