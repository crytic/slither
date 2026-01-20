"""Tests for slither/utils/output.py"""

import pytest
from pathlib import Path

from slither import Slither
from slither.utils.output import (
    OutputConfig,
    set_exclude_location,
    get_exclude_location,
    _convert_to_description,
)

TEST_DATA_DIR = (
    Path(__file__).parent.parent.parent / "e2e" / "printers" / "test_data" / "test_contract_names"
)


@pytest.fixture(autouse=True)
def reset_output_config():
    """Reset OutputConfig before and after each test."""
    set_exclude_location(False)
    yield
    set_exclude_location(False)


@pytest.fixture
def slither_instance(solc_binary_path):
    """Create Slither instance from test contracts."""
    solc_path = solc_binary_path("0.8.0")
    return Slither(str(TEST_DATA_DIR / "C.sol"), solc=solc_path)


def test_exclude_location_setter_getter():
    """Test set_exclude_location and get_exclude_location functions."""
    assert get_exclude_location() is False

    set_exclude_location(True)
    assert get_exclude_location() is True

    set_exclude_location(False)
    assert get_exclude_location() is False


def test_output_config_class():
    """Test that OutputConfig class attribute works correctly."""
    OutputConfig.EXCLUDE_LOCATION = True
    assert OutputConfig.EXCLUDE_LOCATION is True

    OutputConfig.EXCLUDE_LOCATION = False
    assert OutputConfig.EXCLUDE_LOCATION is False


def test_convert_to_description_string():
    """Test _convert_to_description with a plain string."""
    assert _convert_to_description("test string") == "test string"


def test_convert_to_description_contract_with_location(slither_instance):
    """Test _convert_to_description includes location for Contract."""
    contract = slither_instance.get_contract_from_name("C")[0]
    result = _convert_to_description(contract)

    assert "C" in result
    assert "C.sol" in result


def test_convert_to_description_contract_without_location(slither_instance):
    """Test _convert_to_description excludes location when configured."""
    set_exclude_location(True)

    contract = slither_instance.get_contract_from_name("C")[0]
    result = _convert_to_description(contract)

    assert result == "C"
    assert "C.sol" not in result


def test_convert_to_description_function_with_location(slither_instance):
    """Test _convert_to_description uses canonical_name for Function."""
    contract = slither_instance.get_contract_from_name("C")[0]
    function = contract.get_function_from_signature("c_main()")
    result = _convert_to_description(function)

    assert "C.c_main()" in result
    assert "C.sol" in result


def test_convert_to_description_function_without_location(slither_instance):
    """Test _convert_to_description excludes location for Function."""
    set_exclude_location(True)

    contract = slither_instance.get_contract_from_name("C")[0]
    function = contract.get_function_from_signature("c_main()")
    result = _convert_to_description(function)

    assert result == "C.c_main()"
    assert "C.sol" not in result


def test_convert_to_description_node_with_expression(slither_instance):
    """Test _convert_to_description for Node with expression."""
    contract = slither_instance.get_contract_from_name("C")[0]
    function = contract.get_function_from_signature("c_main()")

    # Find a node with an expression (a_main() call)
    node_with_expr = next((n for n in function.nodes if n.expression is not None), None)

    assert node_with_expr is not None, "Expected to find a node with expression"

    result = _convert_to_description(node_with_expr)
    assert str(node_with_expr.expression) in result
    assert "C.sol" in result


def test_convert_to_description_node_without_location(slither_instance):
    """Test _convert_to_description for Node excludes location."""
    set_exclude_location(True)

    contract = slither_instance.get_contract_from_name("C")[0]
    function = contract.get_function_from_signature("c_main()")

    node_with_expr = next((n for n in function.nodes if n.expression is not None), None)

    assert node_with_expr is not None, "Expected to find a node with expression"

    result = _convert_to_description(node_with_expr)
    assert result == str(node_with_expr.expression)
    assert "C.sol" not in result
