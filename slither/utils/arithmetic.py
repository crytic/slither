from slither.exceptions import SlitherException
from slither.utils.integer_conversion import convert_string_to_fraction

# pylint: disable=too-many-branches
def convert_subdenomination(
    value: str, sub: str
) -> int:  # pylint: disable=too-many-return-statements

    decimal_value = convert_string_to_fraction(value)
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
