"""
Test for issue #2140: TypeError when ir.destination.type is unhashable.

When a call destination type is a list (e.g., tuple return types from
low-level calls), the `t in using_for` check raises TypeError because
lists are unhashable. This test verifies the fix handles this gracefully.
"""

from slither.slithir.convert import _type_in_using_for


def test_unhashable_type_in_using_for():
    """Verify unhashable types don't crash the using_for lookup."""
    using_for = {"some_type": []}

    # A list is unhashable and should return False, not raise TypeError
    unhashable_type = ["ElementaryType", "bool"]
    result = _type_in_using_for(unhashable_type, using_for)

    assert result is False


def test_hashable_type_in_using_for():
    """Verify normal hashable types still work correctly."""
    using_for = {"address": ["some_library"]}

    # String is hashable and present
    assert _type_in_using_for("address", using_for) is True

    # String is hashable but not present
    assert _type_in_using_for("uint256", using_for) is False
