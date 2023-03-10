from typing import List, TYPE_CHECKING

from slither.exceptions import SlitherException
from slither.utils.integer_conversion import convert_string_to_fraction


if TYPE_CHECKING:
    from slither.core.declarations import Contract, Function

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


# Number of unchecked arithmetic operation needed to be interesting
THRESHOLD_ARITHMETIC_USAGE = 3


def _unchecked_arithemtic_usage(function: "Function") -> bool:
    """
    Check if the function has more than THRESHOLD_ARITHMETIC_USAGE unchecked arithmetic operation

    Args:
        function:

    Returns:

    """

    # pylint: disable=import-outside-toplevel
    from slither.slithir.operations import Binary

    score = 0
    for node in function.nodes:
        if not node.scope.is_checked:
            for ir in node.irs:
                if isinstance(ir, Binary):
                    score += 1
                    if score >= THRESHOLD_ARITHMETIC_USAGE:
                        return True
    return False


def unchecked_arithemtic_usage(contract: "Contract") -> List["Function"]:
    """
    Return the list of function with some unchecked arithmetics

    Args:
        contract:

    Returns:

    """
    # pylint: disable=import-outside-toplevel
    from slither.core.declarations import Function

    ret: List[Function] = []
    for function in contract.all_functions_called:
        if isinstance(function, Function) and _unchecked_arithemtic_usage(function):
            ret.append(function)
    return ret
