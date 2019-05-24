import re, logging, sys
from slither.utils.colors import red, yellow, set_colorization_enabled

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('Slither.Format')
set_colorization_enabled(True)

class FormatConstableStates:

    @staticmethod
    def format(slither, patches, elements):
        for element in elements:
            FormatConstableStates.create_patch(slither, patches, element['source_mapping']['filename_absolute'], \
                                               element['source_mapping']['filename_relative'], element['name'], \
                                               "constant " + element['name'], element['source_mapping']['start'], \
                                               element['source_mapping']['start'] + element['source_mapping']['length'])

    @staticmethod
    def create_patch(slither, patches, in_file, in_file_relative, match_text, replace_text, modify_loc_start, modify_loc_end):
        in_file_str = slither.source_code[in_file].encode('utf-8')
        old_str_of_interest = in_file_str[modify_loc_start:modify_loc_end]
        (new_str_of_interest, num_repl) = re.subn(match_text, replace_text, old_str_of_interest.decode('utf-8'), 1)
        if num_repl != 0:
            patches[in_file_relative].append({
                "file" : in_file,
                "detector" : "constable-states",
                "start" : modify_loc_start,
                "end" : modify_loc_end,
                "old_string" : old_str_of_interest.decode('utf-8'),
                "new_string" : new_str_of_interest
            })
        else:
            logger.error(red("State variable not found?!"))
            sys.exit(-1)
