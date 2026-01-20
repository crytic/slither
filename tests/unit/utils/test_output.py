"""
Tests for slither/utils/output.py
"""

import pytest
from unittest.mock import MagicMock

from slither.utils.output import (
    OutputConfig,
    set_exclude_location,
    get_exclude_location,
    _convert_to_description,
)


@pytest.fixture(autouse=True)
def reset_output_config():
    """Reset OutputConfig before and after each test."""
    set_exclude_location(False)
    yield
    set_exclude_location(False)


def test_exclude_location_default():
    """Test that exclude_location is False by default."""
    # Reset to default
    set_exclude_location(False)
    assert get_exclude_location() is False


def test_exclude_location_setter_getter():
    """Test set_exclude_location and get_exclude_location functions."""
    # Test setting to True
    set_exclude_location(True)
    assert get_exclude_location() is True

    # Test setting back to False
    set_exclude_location(False)
    assert get_exclude_location() is False


def test_convert_to_description_string():
    """Test _convert_to_description with a plain string."""
    result = _convert_to_description("test string")
    assert result == "test string"


def test_convert_to_description_with_location():
    """Test _convert_to_description includes location by default."""
    # Reset to default (include location)
    set_exclude_location(False)

    # Create a mock object with name and source_mapping
    mock_obj = MagicMock()
    mock_obj.name = "test_function"
    mock_obj.source_mapping = "contracts/Test.sol#10-20"
    # Ensure it's recognized as a SourceMapping
    mock_obj.__class__.__name__ = "Function"

    # Mock the isinstance check for SourceMapping
    from slither.core.source_mapping.source_mapping import SourceMapping

    mock_obj.__class__.__bases__ = (SourceMapping,)

    result = _convert_to_description(mock_obj)
    assert "test_function" in result
    assert "contracts/Test.sol#10-20" in result


def test_convert_to_description_without_location():
    """Test _convert_to_description excludes location when configured."""
    # Set to exclude location
    set_exclude_location(True)

    # Create a mock object with name and source_mapping
    mock_obj = MagicMock()
    mock_obj.name = "test_function"
    mock_obj.source_mapping = "contracts/Test.sol#10-20"

    # Mock the isinstance check for SourceMapping
    from slither.core.source_mapping.source_mapping import SourceMapping

    mock_obj.__class__.__bases__ = (SourceMapping,)

    result = _convert_to_description(mock_obj)
    assert result == "test_function"
    assert "contracts/Test.sol" not in result

    # Clean up
    set_exclude_location(False)


def test_output_config_class():
    """Test that OutputConfig class attribute works correctly."""
    # Test direct access
    OutputConfig.EXCLUDE_LOCATION = True
    assert OutputConfig.EXCLUDE_LOCATION is True

    OutputConfig.EXCLUDE_LOCATION = False
    assert OutputConfig.EXCLUDE_LOCATION is False
