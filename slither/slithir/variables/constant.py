from functools import total_ordering
from decimal import Decimal
from typing import Optional, TYPE_CHECKING, Union

from slither.slithir.variables.variable import SlithIRVariable
from slither.core.solidity_types.elementary_type import ElementaryType, Int, Uint
from slither.utils.arithmetic import convert_subdenomination
from ..exceptions import SlithIRError



if TYPE_CHECKING:
    from slither.core.solidity_types.type import Type

@total_ordering
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
                    if "e" in val or "E" in val:
                        base, expo = val.split("e") if "e" in val else val.split("E")
                        base, expo = Decimal(base), int(expo)
                        # The resulting number must be < 2**256-1, otherwise solc
                        # Would not be able to compile it
                        # 10**77 is the largest exponent that fits
                        # See https://github.com/ethereum/solidity/blob/9e61f92bd4d19b430cb8cb26f1c7cf79f1dff380/libsolidity/ast/Types.cpp#L1281-L1290
                        if expo > 77:
                            if base != Decimal(0):
                                raise SlithIRError(
                                    f"{base}e{expo} is too large to fit in any Solidity integer size"
                                )
                            else:
                                self._val = 0
                        else:
                            self._val = int(Decimal(base) * Decimal(10 ** expo))
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

    def __ne__(self, other):
        return self.value != other

    def __lt__(self, other):
        return self.value < other

    def __repr__(self):
        return "%s" % (str(self.value))
