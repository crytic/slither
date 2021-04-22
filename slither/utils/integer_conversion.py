from decimal import Decimal

from slither.exceptions import SlitherError


def convert_string_to_int(val: str) -> int:
    if val.startswith("0x") or val.startswith("0X"):
        return int(val, 16)

    if "e" in val or "E" in val:
        base, expo = val.split("e") if "e" in val else val.split("E")
        base, expo = Decimal(base), int(expo)
        # The resulting number must be < 2**256-1, otherwise solc
        # Would not be able to compile it
        # 10**77 is the largest exponent that fits
        # See https://github.com/ethereum/solidity/blob/9e61f92bd4d19b430cb8cb26f1c7cf79f1dff380/libsolidity/ast/Types.cpp#L1281-L1290
        if expo > 77:
            if base != Decimal(0):
                raise SlitherError(
                    f"{base}e{expo} is too large to fit in any Solidity integer size"
                )
            return 0
        return int(Decimal(base) * Decimal(10 ** expo))

    return int(Decimal(val))
