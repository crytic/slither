from typing import Dict
import os

from slither.core.declarations import Contract
from slither.core.variables.variable import Variable
from slither.formatters.utils.patches import create_patch
from slither.tools.mutator.utils.testing_generated_mutant import compile_generated_mutant, run_test_suite
from slither.tools.mutator.utils.replace_conditions import replace_string_in_source_file
from slither.tools.mutator.utils.file_handling import create_mutant_file

def remove_assignement(variable: Variable, contract: Contract, result: Dict) -> bool:
    """
    Remove the variable's initial assignement

    :param variable:
    :param contract:
    :param result:
    :return:
    """
    # Retrieve the file
    in_file = contract.source_mapping.filename.absolute
    # Retrieve the source code
    in_file_str = contract.compilation_unit.core.source_code[in_file]

    # Get the string
    start = variable.source_mapping.start
    stop = variable.expression.source_mapping.start
    old_str = in_file_str[start:stop]

    new_str = old_str[: old_str.find("=")]
    line_no = [0]
    create_patch(
        result,
        in_file,
        start,
        stop + variable.expression.source_mapping.length,
        old_str,
        new_str,
        line_no
    )