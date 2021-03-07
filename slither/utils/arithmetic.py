from decimal import Decimal

from slither.exceptions import SlitherException


def convert_subdenomination(
    value: str, sub: str
) -> int:  # pylint: disable=too-many-return-statements

    # to allow 0.1 ether conversion
    if value[0:2] == "0x":
        decimal_value = Decimal(int(value, 16))
    else:
        decimal_value = Decimal(value)
    if sub == "wei":
        return int(decimal_value)
    if sub == "gwei":
        return int(decimal_value * int(1e9))
    if sub == "szabo":
        return int(decimal_value * int(1e12))
    if sub == "finney":
        return int(decimal_value * int(1e15))
    if sub == "ether":
        return int(decimal_value * int(1e18))
    if sub == "seconds":
        return int(decimal_value)
    if sub == "minutes":
        return int(decimal_value * 60)
    if sub == "hours":
        return int(decimal_value * 60 * 60)
    if sub == "days":
        return int(decimal_value * 60 * 60 * 24)
    if sub == "weeks":
        return int(decimal_value * 60 * 60 * 24 * 7)
    if sub == "years":
        return int(decimal_value * 60 * 60 * 24 * 7 * 365)

    raise SlitherException(f"Subdemonination conversion impossible {decimal_value} {sub}")
