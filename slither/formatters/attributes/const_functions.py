import re
from slither.formatters.exceptions import FormatError
from slither.formatters.utils.patches import create_patch


def custom_format(slither, result):
    elements = result["elements"]
    for element in elements:
        if element["type"] != "function":
            # Skip variable elements
            continue
        target_contract = slither.get_contract_from_name(
            element["type_specific_fields"]["parent"]["name"]
        )
        if target_contract:
            function = target_contract.get_function_from_signature(
                element["type_specific_fields"]["signature"]
            )
            if function:
                _patch(
                    slither,
                    result,
                    element["source_mapping"]["filename_absolute"],
                    int(
                        function.parameters_src.source_mapping["start"]
                        + function.parameters_src.source_mapping["length"]
                    ),
                    int(function.returns_src.source_mapping["start"]),
                )


def _patch(slither, result, in_file, modify_loc_start, modify_loc_end):
    in_file_str = slither.source_code[in_file].encode("utf8")
    old_str_of_interest = in_file_str[modify_loc_start:modify_loc_end]
    # Find the keywords view|pure|constant and remove them
    m = re.search("(view|pure|constant)", old_str_of_interest.decode("utf-8"))
    if m:
        create_patch(
            result,
            in_file,
            modify_loc_start + m.span()[0],
            modify_loc_start + m.span()[1],
            m.groups(0)[0],  # this is view|pure|constant
            "",
        )
    else:
        raise FormatError(
            "No view/pure/constant specifier exists. Regex failed to remove specifier!"
        )
