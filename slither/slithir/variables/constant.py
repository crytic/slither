from functools import total_ordering
from typing import Optional, Union

from slither.core.solidity_types.elementary_type import ElementaryType, Int, Uint
from slither.slithir.variables.variable import SlithIRVariable
from slither.utils.arithmetic import convert_subdenomination
from slither.utils.integer_conversion import convert_string_to_int


@total_ordering
class Constant(SlithIRVariable):
    def __init__(
        self,
        val: str,
        constant_type: Optional[ElementaryType] = None,
        subdenomination: Optional[str] = None,
    ) -> None:  # pylint: disable=too-many-branches
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
                self._val: Union[bool, int, str] = convert_string_to_int(val)
            elif constant_type.type == "bool":
                self._val = (val == "true") | (val == "True")
            else:
                self._val = val
        else:
            if val.isdigit():
                self._type = ElementaryType("uint256")
                self._val = convert_string_to_int(val)
            else:
                self._type = ElementaryType("string")
                self._val = val

        self._name = str(self._val)

    @property
    def value(self) -> Union[bool, int, str]:
        """
        Return the value.
        If the expression was an hexadecimal delcared as hex'...'
        return a str
        Returns:
            (str | int | bool)
        """
        return self._val

    @property
    def original_value(self) -> str:
        """
        Return the string representation of the value
        :return: str
        """
        return self._original_value

    def __str__(self) -> str:
        return str(self.value)

    def __eq__(self, other: object) -> bool:
        return self.value == other

    def __ne__(self, other: object) -> bool:
        return self.value != other

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, (Constant, str)):
            raise NotImplementedError
        return self.value < other  # type: ignore

    def __repr__(self) -> str:
        return f"{str(self.value)}"

    def __hash__(self) -> int:
        return self._val.__hash__()
