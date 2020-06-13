from decimal import Decimal
from typing import Optional, TYPE_CHECKING, Union

from slither.slithir.variables.variable import SlithIRVariable
from slither.core.solidity_types.elementary_type import ElementaryType, Int, Uint
from slither.utils.arithmetic import convert_subdenomination

if TYPE_CHECKING:
    from slither.core.solidity_types.type import Type


class Constant(SlithIRVariable):
    def __init__(
        self, val: str, type: Optional["Type"] = None, subdenomination: Optional[str] = None
    ):
        super(Constant, self).__init__()
        assert isinstance(val, str)

        self._original_value = val
        self._subdenomination = subdenomination
        self._val: Union[int, bool, str]

        if subdenomination:
            val = str(convert_subdenomination(val, subdenomination))

        if type:
            assert isinstance(type, ElementaryType)
            self._type = type
            if type.type in Int + Uint + ["address"]:
                if val.startswith("0x") or val.startswith("0X"):
                    self._val = int(val, 16)
                else:
                    if "e" in val:
                        base, expo = val.split("e")
                        self._val = int(Decimal(base) * (10 ** int(expo)))
                    elif "E" in val:
                        base, expo = val.split("E")
                        self._val = int(Decimal(base) * (10 ** int(expo)))
                    else:
                        self._val = int(Decimal(val))
            elif type.type == "bool":
                self._val = (val == "true") | (val == "True")
            else:
                self._val = val
        else:
            if val.isdigit():
                self._type = ElementaryType("uint256")
                self._val = int(Decimal(val))
            else:
                self._type = ElementaryType("string")
                self._val = val

    @property
    def value(self) -> Union[str, int, bool]:
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

    def __str__(self):
        return str(self.value)

    @property
    def name(self) -> str:
        return str(self)

    @name.setter
    def name(self, name: str):
        self._name = name

    def __eq__(self, other):
        return self.value == other

    def __hash__(self):
        return hash(self.value)
