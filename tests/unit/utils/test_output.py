"""
Tests for slither/utils/output.py
"""
from unittest.mock import MagicMock

from slither.utils.output import (
    set_exclude_location,
    get_exclude_location,
    _convert_to_description,
)


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
    """Test that strings pass through unchanged."""
    result = _convert_to_description("test string")
    assert result == "test string"


def test_convert_to_description_with_location():
    """Test _convert_to_description includes location when exclude_location is False."""
    set_exclude_location(False)

    # Create a mock object with canonical_name and source_mapping
    mock_obj = MagicMock()
    mock_obj.canonical_name = "TestContract.testFunction"
    mock_obj.source_mapping = "test.sol#10-15"

    # Mock isinstance check for SourceMapping
    from slither.core.source_mapping.source_mapping import SourceMapping
    mock_obj.__class__ = type("MockSourceMapping", (SourceMapping,), {})

    result = _convert_to_description(mock_obj)
    assert "TestContract.testFunction" in result
    assert "test.sol#10-15" in result


def test_convert_to_description_without_location():
    """Test _convert_to_description excludes location when exclude_location is True."""
    set_exclude_location(True)

    # Create a mock object with canonical_name and source_mapping
    mock_obj = MagicMock()
    mock_obj.canonical_name = "TestContract.testFunction"
    mock_obj.source_mapping = "test.sol#10-15"

    # Mock isinstance check for SourceMapping
    from slither.core.source_mapping.source_mapping import SourceMapping
    mock_obj.__class__ = type("MockSourceMapping", (SourceMapping,), {})

    result = _convert_to_description(mock_obj)
    assert result == "TestContract.testFunction"
    assert "test.sol" not in result

    # Reset
    set_exclude_location(False)
