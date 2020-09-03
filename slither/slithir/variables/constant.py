from functools import total_ordering
from decimal import Decimal

from slither.slithir.variables.variable import SlithIRVariable
from slither.slithir.exceptions import SlithIRError
from slither.core.solidity_types.elementary_type import ElementaryType, Int, Uint
from slither.utils.arithmetic import convert_subdenomination


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
                            self._val = 0
                        else:
                            self._val = int(Decimal(base) * Decimal(10 ** expo))
                    else:
                        self._val = int(Decimal(val))
            elif constant_type.type == "bool":
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
        return "%s" % (str(self.value))
