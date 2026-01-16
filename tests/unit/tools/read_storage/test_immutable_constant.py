"""
Tests for immutable and constant variable support in slither-read-storage
"""
import pytest
from pathlib import Path

from slither import Slither
from slither.tools.read_storage.read_storage import SlitherReadStorage


TEST_CONTRACT = """
pragma solidity ^0.8.0;

contract TestConstantImmutable {
    // Constant variables
    bytes32 public constant BYTES_CONSTANT = 0x1111111111111111111111111111111111111111111111111111111111111111;
    uint256 public constant UINT_CONSTANT = 12345;
    address public constant ADDRESS_CONSTANT = 0x2222222222222222222222222222222222222222;
    bool public constant BOOL_CONSTANT = true;

    // Private constant
    uint256 private constant PRIVATE_CONSTANT = 99999;

    // Immutable variables
    address public immutable someAddress;
    uint256 public immutable someUint;

    // Private immutable
    bytes32 private immutable privateBytes;

    // Regular storage variable
    uint256 public someStorageVar = 3;

    constructor() {
        someAddress = 0x3333333333333333333333333333333333333333;
        someUint = 42;
        privateBytes = 0x4444444444444444444444444444444444444444444444444444444444444444;
    }
}
"""


@pytest.fixture
def slither_from_source(tmp_path):
    """Create a Slither instance from source code."""
    file_path = tmp_path / "test_constant_immutable.sol"
    file_path.write_text(TEST_CONTRACT)
    return Slither(str(file_path))


def test_immutable_constant_detection(slither_from_source):
    """Test that immutable and constant variables are detected."""
    contracts = slither_from_source.contracts

    srs = SlitherReadStorage(contracts, max_depth=20)
    srs.include_immutable = True
    srs.get_all_storage_variables()

    # Check that we found the regular storage variable
    assert len(srs.target_variables) >= 1
    storage_var_names = [var.name for _, var in srs.target_variables]
    assert "someStorageVar" in storage_var_names

    # Check that we found immutable variables
    assert len(srs.immutable_variables) >= 2
    immutable_names = [var.name for _, var in srs.immutable_variables]
    assert "someAddress" in immutable_names
    assert "someUint" in immutable_names
    assert "privateBytes" in immutable_names

    # Check that we found constant variables
    assert len(srs.constant_variables) >= 4
    constant_names = [var.name for _, var in srs.constant_variables]
    assert "BYTES_CONSTANT" in constant_names
    assert "UINT_CONSTANT" in constant_names
    assert "ADDRESS_CONSTANT" in constant_names
    assert "BOOL_CONSTANT" in constant_names
    assert "PRIVATE_CONSTANT" in constant_names


def test_immutable_disabled_by_default(slither_from_source):
    """Test that immutable/constant detection is disabled by default."""
    contracts = slither_from_source.contracts

    srs = SlitherReadStorage(contracts, max_depth=20)
    # include_immutable defaults to False
    srs.get_all_storage_variables()

    # Should only find storage variables, not immutable/constant
    assert len(srs.immutable_variables) == 0
    assert len(srs.constant_variables) == 0
    assert len(srs.target_variables) >= 1


def test_storage_layout_includes_immutable(slither_from_source):
    """Test that storage layout includes immutable/constant when enabled."""
    contracts = slither_from_source.contracts

    srs = SlitherReadStorage(contracts, max_depth=20)
    srs.include_immutable = True
    srs.get_all_storage_variables()
    srs.get_storage_layout()

    slot_info = srs.slot_info

    # Check regular storage variable is in slot_info
    assert "someStorageVar" in slot_info
    assert slot_info["someStorageVar"].slot >= 0

    # Check immutable variables are in slot_info with slot=-1
    assert "someAddress" in slot_info
    assert slot_info["someAddress"].slot == -1
    assert "(immutable)" in slot_info["someAddress"].type_string

    # Check constant variables are in slot_info with slot=-1
    assert "UINT_CONSTANT" in slot_info
    assert slot_info["UINT_CONSTANT"].slot == -1
    assert "(constant)" in slot_info["UINT_CONSTANT"].type_string


def test_constant_value_extraction(slither_from_source):
    """Test that constant values are extracted from expressions."""
    contracts = slither_from_source.contracts

    srs = SlitherReadStorage(contracts, max_depth=20)
    srs.include_immutable = True
    srs.get_all_storage_variables()
    srs.get_storage_layout()

    slot_info = srs.slot_info

    # Check that constant values are extracted
    assert "UINT_CONSTANT" in slot_info
    # The value should be extracted from the expression
    assert slot_info["UINT_CONSTANT"].value == 12345 or slot_info["UINT_CONSTANT"].value == "12345"

    assert "BOOL_CONSTANT" in slot_info
    # Bool constant should be True
    assert slot_info["BOOL_CONSTANT"].value in [True, "true", "True"]
