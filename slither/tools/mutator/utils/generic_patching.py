from typing import Dict

from slither.core.declarations import Contract
from slither.core.variables.variable import Variable
from slither.formatters.utils.patches import create_patch


def remove_assignement(variable: Variable, contract: Contract, result: Dict):
    """
    Remove the variable's initial assignement

    :param variable:
    :param contract:
    :param result:
    :return:
    """
    # Retrieve the file
    in_file = contract.source_mapping["filename_absolute"]
    # Retrieve the source code
    in_file_str = contract.slither.source_code[in_file]

    # Get the string
    start = variable.source_mapping["start"]
    stop = variable.expression.source_mapping["start"]
    old_str = in_file_str[start:stop]

    new_str = old_str[: old_str.find("=")]

    create_patch(
        result,
        in_file,
        start,
        stop + variable.expression.source_mapping["length"],
        old_str,
        new_str,
    )
