"""Tests for slither/core/expressions/literal.py"""

from slither.core.expressions.literal import Literal, _NUMERIC_TYPES
from slither.core.solidity_types.elementary_type import ElementaryType


class TestLiteralCaching:
    """Test Literal.__str__ caching behavior."""

    def test_numeric_string_type_caches(self):
        """Numeric literals with string type should cache converted value."""
        lit = Literal("0xff", "uint256")
        assert lit._cached_str == "255"
        assert str(lit) == "255"

    def test_hex_value_converted(self):
        """Hex values should be converted to decimal."""
        lit = Literal("0x10", "uint256")
        assert str(lit) == "16"

    def test_scientific_notation_converted(self):
        """Scientific notation should be converted."""
        lit = Literal("1e18", "uint256")
        assert str(lit) == "1000000000000000000"

    def test_elementary_type_not_cached(self):
        """ElementaryType inputs should NOT be cached (preserves original behavior)."""
        elem_type = ElementaryType("uint256")
        lit = Literal("100", elem_type)
        assert lit._cached_str is None
        # Original behavior: ElementaryType not in string list, so returns raw value
        assert str(lit) == "100"

    def test_string_literal_not_cached(self):
        """String literals should not be cached."""
        lit = Literal("hello world", "string")
        assert lit._cached_str is None
        assert str(lit) == "hello world"

    def test_subdenomination_uses_converted_value(self):
        """Literals with subdenomination should use converted_value, not cache."""
        lit = Literal("1", "uint256", subdenomination="ether")
        assert lit._cached_str is None  # Not cached when subdenomination set
        assert str(lit) == "1000000000000000000"

    def test_address_type_cached(self):
        """Address type should be cached."""
        lit = Literal("0x1234", "address")
        assert lit._cached_str == "4660"
        assert str(lit) == "4660"

    def test_int_types_cached(self):
        """Signed int types should be cached."""
        lit = Literal("100", "int256")
        assert lit._cached_str == "100"

    def test_numeric_types_frozenset(self):
        """Verify _NUMERIC_TYPES contains expected types."""
        assert "uint256" in _NUMERIC_TYPES
        assert "int256" in _NUMERIC_TYPES
        assert "address" in _NUMERIC_TYPES
        assert "string" not in _NUMERIC_TYPES
        assert "bytes32" not in _NUMERIC_TYPES


class TestLiteralEquality:
    """Test Literal.__eq__ behavior."""

    def test_equal_literals(self):
        """Literals with same value and subdenomination are equal."""
        lit1 = Literal("100", "uint256")
        lit2 = Literal("100", "uint256")
        assert lit1 == lit2

    def test_different_values(self):
        """Literals with different values are not equal."""
        lit1 = Literal("100", "uint256")
        lit2 = Literal("200", "uint256")
        assert lit1 != lit2

    def test_different_subdenomination(self):
        """Literals with different subdenominations are not equal."""
        lit1 = Literal("1", "uint256")
        lit2 = Literal("1", "uint256", subdenomination="ether")
        assert lit1 != lit2

    def test_not_equal_to_non_literal(self):
        """Literal should not equal non-Literal objects."""
        lit = Literal("100", "uint256")
        assert lit != "100"
        assert lit != 100
