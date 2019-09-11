import re
from ..exceptions import FormatError, FormatImpossible
from ..utils.patches import create_patch

def format(slither, result):
    elements = result['elements']
    for element in elements:
        if not element.expression:
            raise FormatImpossible(f'{element.name} is uninitialized and cannot become constant.')
        _patch(slither, result, element['source_mapping']['filename_absolute'],
               element['name'],
               "constant " + element['name'],
               element['source_mapping']['start'],
               element['source_mapping']['start'] + element['source_mapping']['length'])


def _patch(slither, result, in_file, match_text, replace_text, modify_loc_start, modify_loc_end):
    in_file_str = slither.source_code[in_file].encode('utf8')
    old_str_of_interest = in_file_str[modify_loc_start:modify_loc_end]
    # Add keyword `constant` before the variable name
    (new_str_of_interest, num_repl) = re.subn(match_text, replace_text, old_str_of_interest.decode('utf-8'), 1)
    if num_repl != 0:
        create_patch(result,
                     in_file,
                     modify_loc_start,
                     modify_loc_end,
                     old_str_of_interest,
                     new_str_of_interest)

    else:
        raise FormatError("State variable not found?!")

