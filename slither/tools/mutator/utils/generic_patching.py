from typing import Dict
import os

from slither.core.declarations import Contract
from slither.core.variables.variable import Variable
from slither.formatters.utils.patches import create_patch
from slither.tools.mutator.utils.testing_generated_mutant import compile_generated_mutant, run_test_suite
from slither.tools.mutator.utils.replace_conditions import replace_string_in_source_file
from slither.tools.mutator.utils.file_handling import create_mutant_file

def remove_assignement(variable: Variable, contract: Contract, result: Dict, test_cmd: str, test_dir: str) -> bool:
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
    
    replace_string_in_source_file(in_file, in_file_str[variable.source_mapping.start + old_str.find("="):variable.source_mapping.end], '')

    # compile and run tests before the mutant generated before patching
    if compile_generated_mutant(in_file):
        if run_test_suite(test_cmd, test_dir):
            # create_mutant_file(in_file, )
            create_patch(
                result,
                in_file,
                start,
                stop + variable.expression.source_mapping.length,
                old_str,
                new_str,
            )
            return True