import re, logging
from slither.utils.colors import red, yellow, set_colorization_enabled

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('Slither.Format')
set_colorization_enabled(True)

class FormatConstantFunction:

    @staticmethod
    def format(slither, patches, elements):
        for element in elements:
            if element['type'] != "function":
                # Skip variable elements
                continue
            Found = False
            for contract in slither.contracts:
                if not Found:
                    for function in contract.functions:
                        if contract.name == element['type_specific_fields']['parent']['name'] and function.name == element['name']:
                            FormatConstantFunction.create_patch(slither, patches, element['source_mapping']['filename_absolute'], element['source_mapping']['filename_relative'], ["view","pure","constant"], "", int(function.parameters_src.source_mapping['start']), int(function.returns_src.source_mapping['start']))
                            Found = True

    @staticmethod
    def create_patch(slither, patches, in_file, in_file_relative, match_text, replace_text, modify_loc_start, modify_loc_end):
        in_file_str = slither.source_code[in_file].encode('utf-8')
        old_str_of_interest = in_file_str[modify_loc_start:modify_loc_end]
        m = re.search("(view|pure|constant)", old_str_of_interest.decode('utf-8'))
        if m:
            patches[in_file_relative].append({
                "file" : in_file,
                "detector" : "constant-function",
                "start" : modify_loc_start + m.span()[0],
                "end" : modify_loc_start + m.span()[1],
                "old_string" : m.groups(0)[0],
                "new_string" : replace_text
            })
        else:
            logger.error(red("No view/pure/constant specifier exists. Regex failed to remove specifier!"))
            sys.exit(-1)
