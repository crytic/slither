"""Tests for Type.__eq__ methods (verifies PR #2935 optimizations)."""

from slither.core.solidity_types.elementary_type import ElementaryType
from slither.core.solidity_types.array_type import ArrayType
from slither.core.solidity_types.mapping_type import MappingType
from slither.core.solidity_types.function_type import FunctionType
from slither.core.solidity_types.type_information import TypeInformation
from slither.core.variables.function_type_variable import FunctionTypeVariable


class TestElementaryTypeEquality:
    """Test ElementaryType.__eq__ behavior."""

    def test_equal_types(self):
        """ElementaryTypes with same type string are equal."""
        t1 = ElementaryType("uint256")
        t2 = ElementaryType("uint256")
        assert t1 == t2

    def test_different_types(self):
        """ElementaryTypes with different type strings are not equal."""
        t1 = ElementaryType("uint256")
        t2 = ElementaryType("uint128")
        assert t1 != t2

    def test_not_equal_to_non_type(self):
        """ElementaryType should not equal non-ElementaryType objects."""
        t = ElementaryType("uint256")
        assert t != "uint256"
        assert t != 256


class TestArrayTypeEquality:
    """Test ArrayType.__eq__ behavior."""

    def test_equal_dynamic_arrays(self):
        """Dynamic arrays of same type are equal."""
        t1 = ArrayType(ElementaryType("uint256"), None)
        t2 = ArrayType(ElementaryType("uint256"), None)
        assert t1 == t2

    def test_equal_fixed_arrays(self):
        """Fixed arrays of same type and length are equal."""
        t1 = ArrayType(ElementaryType("uint256"), 10)
        t2 = ArrayType(ElementaryType("uint256"), 10)
        assert t1 == t2

    def test_different_element_types(self):
        """Arrays with different element types are not equal."""
        t1 = ArrayType(ElementaryType("uint256"), None)
        t2 = ArrayType(ElementaryType("uint128"), None)
        assert t1 != t2

    def test_different_lengths(self):
        """Arrays with different lengths are not equal."""
        t1 = ArrayType(ElementaryType("uint256"), 10)
        t2 = ArrayType(ElementaryType("uint256"), 20)
        assert t1 != t2

    def test_fixed_vs_dynamic(self):
        """Fixed and dynamic arrays are not equal."""
        t1 = ArrayType(ElementaryType("uint256"), 10)
        t2 = ArrayType(ElementaryType("uint256"), None)
        assert t1 != t2

    def test_not_equal_to_non_type(self):
        """ArrayType should not equal non-ArrayType objects."""
        t = ArrayType(ElementaryType("uint256"), None)
        assert t != "uint256[]"


class TestMappingTypeEquality:
    """Test MappingType.__eq__ behavior."""

    def test_equal_mappings(self):
        """Mappings with same key and value types are equal."""
        t1 = MappingType(ElementaryType("address"), ElementaryType("uint256"))
        t2 = MappingType(ElementaryType("address"), ElementaryType("uint256"))
        assert t1 == t2

    def test_different_key_types(self):
        """Mappings with different key types are not equal."""
        t1 = MappingType(ElementaryType("address"), ElementaryType("uint256"))
        t2 = MappingType(ElementaryType("bytes32"), ElementaryType("uint256"))
        assert t1 != t2

    def test_different_value_types(self):
        """Mappings with different value types are not equal."""
        t1 = MappingType(ElementaryType("address"), ElementaryType("uint256"))
        t2 = MappingType(ElementaryType("address"), ElementaryType("uint128"))
        assert t1 != t2

    def test_not_equal_to_non_type(self):
        """MappingType should not equal non-MappingType objects."""
        t = MappingType(ElementaryType("address"), ElementaryType("uint256"))
        assert t != "mapping(address => uint256)"


class TestFunctionTypeEquality:
    """Test FunctionType.__eq__ behavior."""

    def test_equal_function_types(self):
        """FunctionTypes with same params and returns are equal."""
        t1 = FunctionType([], [])
        t2 = FunctionType([], [])
        assert t1 == t2

    def test_different_params(self):
        """FunctionTypes with different params are not equal."""
        var1 = FunctionTypeVariable()
        var1.set_type(ElementaryType("uint256"))
        t1 = FunctionType([var1], [])
        t2 = FunctionType([], [])
        assert t1 != t2

    def test_not_equal_to_non_type(self):
        """FunctionType should not equal non-FunctionType objects."""
        t = FunctionType([], [])
        assert t != "function()"


class TestTypeInformationEquality:
    """Test TypeInformation.__eq__ behavior."""

    def test_equal_type_info(self):
        """TypeInformation with same underlying type are equal."""
        t1 = TypeInformation(ElementaryType("uint256"))
        t2 = TypeInformation(ElementaryType("uint256"))
        assert t1 == t2

    def test_different_type_info(self):
        """TypeInformation with different underlying types are not equal."""
        t1 = TypeInformation(ElementaryType("uint256"))
        t2 = TypeInformation(ElementaryType("uint128"))
        assert t1 != t2

    def test_not_equal_to_non_type(self):
        """TypeInformation should not equal non-TypeInformation objects."""
        t = TypeInformation(ElementaryType("uint256"))
        assert t != "type(uint256)"
