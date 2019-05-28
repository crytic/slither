import re, logging
from slither.utils.colors import red, yellow, set_colorization_enabled

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('Slither.Format')
set_colorization_enabled(True)

class FormatExternalFunction:

    @staticmethod
    def format (slither, patches, elements):
        for element in elements:
            target_contract = slither.get_contract_from_name(element['type_specific_fields']['parent']['name'])
            if target_contract:
                for function in target_contract.functions:
                    if function.name == element['name']:
                        # If function parameters are written to in function body then we cannot convert this function
                        # to external because external function parameters are allocated in calldata region which is
                        # non-modifiable. See https://solidity.readthedocs.io/en/develop/types.html#data-location
                        # Remove this once PR #257 is merged
                        if not FormatExternalFunction.function_parameters_written(function):
                            FormatExternalFunction.create_patch(slither, patches, \
                                                                element['source_mapping']['filename_absolute'], \
                                                                element['source_mapping']['filename_relative'], \
                                                                "public", "external", \
                                                                int(function.parameters_src.source_mapping['start']), \
                                                                int(function.returns_src.source_mapping['start']))
                            break

    @staticmethod
    def create_patch(slither, patches, in_file, in_file_relative, match_text, replace_text, modify_loc_start, modify_loc_end):
        in_file_str = slither.source_code[in_file].encode('utf-8')
        old_str_of_interest = in_file_str[modify_loc_start:modify_loc_end]
        # Search for 'public' keyword which is in-between the function name and modifier name (if present)
        # regex: 'public' could have spaces around or be at the end of the line
        m = re.search(r'((\spublic)\s+)|(\spublic)$|(\)public)$', old_str_of_interest.decode('utf-8'))
        if m is None:
            # No visibility specifier exists; public by default.
            patches[in_file_relative].append({
                "file" : in_file,
                "detector" : "external-function",
                # start after the function definition's closing paranthesis
                "start" : modify_loc_start + len(old_str_of_interest.decode('utf-8').split(')')[0]) + 1,
                # end is same as start because we insert the keyword `external` at that location
                "end" : modify_loc_start + len(old_str_of_interest.decode('utf-8').split(')')[0]) + 1,
                "old_string" : "",
                "new_string" : " " + replace_text # replace_text is `external`
            })
        else:
            patches[in_file_relative].append({
                "file" : in_file,
                "detector" : "external-function",
                # start at the keyword `public`
                "start" : modify_loc_start + m.span()[0] + 1,
                # end after the keyword `public` = start + len('public'')
                "end" : modify_loc_start + m.span()[0] + 1 + 6,
                "old_string" : match_text, # match_text is `public`
                "new_string" : replace_text # replace_text is `external`
            })

    @staticmethod
    def function_parameters_written(function):
        for node in function.nodes:
            if any (var.name == parameter.name for var in node.local_variables_written for parameter in function.parameters):
                return True
        return False
            
