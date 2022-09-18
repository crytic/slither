from fractions import Fraction
from functools import total_ordering

from slither.core.solidity_types.elementary_type import ElementaryType, Int, Uint
from slither.slithir.variables.variable import SlithIRVariable
from slither.utils.arithmetic import convert_subdenomination
from slither.utils.integer_conversion import convert_string_to_int


@total_ordering
class Constant(SlithIRVariable):
    def __init__(
        self, val, constant_type=None, subdenomination=None
    ):  # pylint: disable=too-many-branches
        super().__init__()
        assert isinstance(val, str)

        self._original_value = val
        self._subdenomination = subdenomination

        if subdenomination:
            val = str(convert_subdenomination(val, subdenomination))

        if constant_type:  # pylint: disable=too-many-nested-blocks
            assert isinstance(constant_type, ElementaryType)
            self._type = constant_type
            if constant_type.type in Int + Uint + ["address"]:
                self._val = convert_string_to_int(val)
            elif constant_type.type == "bool":
                self._val = (val == "true") | (val == "True")
            else:
                self._val = val
        else:
            if val.isdigit():
                self._type = ElementaryType("uint256")
                self._val = int(Fraction(val))
            else:
                self._type = ElementaryType("string")
                self._val = val

    @property
    def value(self):
        """
        Return the value.
        If the expression was an hexadecimal delcared as hex'...'
        return a str
        Returns:
            (str | int | bool)
        """
        return self._val

    @property
    def original_value(self):
        """
        Return the string representation of the value
        :return: str
        """
        return self._original_value

    def __str__(self):
        return str(self.value)

    @property
    def name(self):
        return str(self)

    def __eq__(self, other):
        return self.value == other

    def __ne__(self, other):
        return self.value != other

    def __lt__(self, other):
        return self.value < other

    def __repr__(self):
        return f"{str(self.value)}"

    def __hash__(self) -> int:
        return self._val.__hash__()
