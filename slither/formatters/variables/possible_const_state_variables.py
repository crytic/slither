import re

from slither.core.compilation_unit import SlitherCompilationUnit
from slither.formatters.exceptions import FormatError, FormatImpossible
from slither.formatters.utils.patches import create_patch


def custom_format(compilation_unit: SlitherCompilationUnit, result):
    elements = result["elements"]
    for element in elements:

        # TODO: decide if this should be changed in the constant detector
        contract_name = element["type_specific_fields"]["parent"]["name"]
        contract = compilation_unit.get_contract_from_name(contract_name)
        var = contract.get_state_variable_from_name(element["name"])
        if not var.expression:
            raise FormatImpossible(f"{var.name} is uninitialized and cannot become constant.")

        _patch(
            compilation_unit,
            result,
            element["source_mapping"]["filename_absolute"],
            element["name"],
            "constant " + element["name"],
            element["source_mapping"]["start"],
            element["source_mapping"]["start"] + element["source_mapping"]["length"],
        )


def _patch(  # pylint: disable=too-many-arguments
    compilation_unit: SlitherCompilationUnit,
    result,
    in_file,
    match_text,
    replace_text,
    modify_loc_start,
    modify_loc_end,
):
    in_file_str = compilation_unit.core.source_code[in_file].encode("utf8")
    old_str_of_interest = in_file_str[modify_loc_start:modify_loc_end]
    # Add keyword `constant` before the variable name
    (new_str_of_interest, num_repl) = re.subn(
        match_text, replace_text, old_str_of_interest.decode("utf-8"), 1
    )
    if num_repl != 0:
        create_patch(
            result,
            in_file,
            modify_loc_start,
            modify_loc_end,
            old_str_of_interest,
            new_str_of_interest,
        )

    else:
        raise FormatError("State variable not found?!")
