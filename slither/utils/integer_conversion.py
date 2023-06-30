from fractions import Fraction
from typing import Union

from slither.exceptions import SlitherError


def convert_string_to_fraction(val: Union[str, bytes, int]) -> Fraction:
    if isinstance(val, bytes):
        return int.from_bytes(val, byteorder="big")
    if isinstance(val, int):
        return Fraction(val)
    if val.startswith(("0x", "0X")):
        return Fraction(int(val, 16))

    # Fractions do not support underscore separators (on Python <3.11)
    val = val.replace("_", "")

    if "e" in val or "E" in val:
        base, expo = val.split("e") if "e" in val else val.split("E")
        base, expo = Fraction(base), int(expo)
        # The resulting number must be < 2**256-1, otherwise solc
        # Would not be able to compile it
        # 10**77 is the largest exponent that fits
        # See https://github.com/ethereum/solidity/blob/9e61f92bd4d19b430cb8cb26f1c7cf79f1dff380/libsolidity/ast/Types.cpp#L1281-L1290
        if expo > 77:
            if base != Fraction(0):
                raise SlitherError(
                    f"{base}e{expo} is too large to fit in any Solidity integer size"
                )
            return 0
        return Fraction(base) * Fraction(10**expo)

    return Fraction(val)


def convert_string_to_int(val: Union[str, int]) -> int:
    return int(convert_string_to_fraction(val))
