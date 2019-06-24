import re
from slither.exceptions import SlitherException
from ..utils.patches import create_patch

class FormatConstantFunction:

    @staticmethod
    def format(slither, patches, elements):
        for element in elements:
            if element['type'] != "function":
                # Skip variable elements
                continue
            target_contract = slither.get_contract_from_name(element['type_specific_fields']['parent']['name'])
            if target_contract:
                for function in target_contract.functions:
                    if function.name == element['name']:
                        FormatConstantFunction.create_patch(slither, patches,
                                                            element['source_mapping']['filename_absolute'],
                                                            element['source_mapping']['filename_relative'],
                                                            int(function.parameters_src.source_mapping['start']),
                                                            int(function.returns_src.source_mapping['start']))
                        break

    @staticmethod
    def create_patch(slither, patches, in_file, in_file_relative, modify_loc_start, modify_loc_end):
        in_file_str = slither.source_code[in_file].encode('utf-8')
        old_str_of_interest = in_file_str[modify_loc_start:modify_loc_end]
        m = re.search("(view|pure|constant)", old_str_of_interest.decode('utf-8'))
        if m:
            create_patch(patches,
                         "constant-function",
                         in_file_relative,
                         in_file,
                         modify_loc_start + m.span()[0],
                         modify_loc_start + m.span()[1],
                         m.groups(0)[0],
                         "")
        else:
            raise SlitherException("No view/pure/constant specifier exists. Regex failed to remove specifier!")
