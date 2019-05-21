import re

class FormatExternalFunction:

    @staticmethod
    def format (slither, patches, elements):
        for element in elements:
            Found = False
            for contract in slither.contracts:
                if not Found and contract.name == element['type_specific_fields']['parent']['name']:
                    for function in contract.functions:
                        if function.name == element['name']:
                            # If function parameters are written to in function body then we cannot convert this function
                            # to external because external function parameters are allocated in calldata region which is
                            # non-modifiable. See https://solidity.readthedocs.io/en/develop/types.html#data-location
                            if not FormatExternalFunction.function_parameters_written(function):
                                FormatExternalFunction.create_patch(slither, patches, element['source_mapping']['filename_absolute'], "public", "external", int(function.parameters_src.source_mapping['start']), int(function.returns_src.source_mapping['start']))
                                Found = True
                                break

    @staticmethod
    def create_patch(slither, patches, in_file, match_text, replace_text, modify_loc_start, modify_loc_end):
        in_file_str = slither.source_code[in_file]
        old_str_of_interest = in_file_str[modify_loc_start:modify_loc_end]
        m = re.search("public", old_str_of_interest)
        if m is None:
            # No visibility specifier exists; public by default.
            patches[in_file].append({
                "detector" : "external-function",
                "start" : modify_loc_start + len(old_str_of_interest.split(')')[0]) + 1,
                "end" : modify_loc_start + len(old_str_of_interest.split(')')[0]) + 1,
                "old_string" : "",
                "new_string" : " " + replace_text
            })
        else:
            patches[in_file].append({
                "detector" : "external-function",
                "start" : modify_loc_start + m.span()[0],
                "end" : modify_loc_start + m.span()[1],
                "old_string" : match_text,
                "new_string" : replace_text
            })

    @staticmethod
    def function_parameters_written(function):
        for node in function.nodes:
            if any (var.name == parameter.name for var in node.local_variables_written for parameter in function.parameters):
                return True
        return False
            
