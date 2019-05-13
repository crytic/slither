import re

class FormatExternalFunction:

    @staticmethod
    def format (slither, patches, elements):
        for element in elements:
            Found = False
            for contract in slither.contracts:
                if not Found and contract.name == element['contract']['name']:
                    for function in contract.functions:
                        if function.name == element['name']:
                            # If function parameters are written to in function body then we cannot convert this function
                            # to external because external function parameters are allocated in calldata region which is
                            # non-modifiable. See https://solidity.readthedocs.io/en/develop/types.html#data-location
                            if not FormatExternalFunction.function_parameters_written(function):
                                FormatExternalFunction.create_patch(slither, patches, element['source_mapping']['filename_absolute'], "public", "external", int(function.parameters_src.split(':')[0]), int(function.returns_src.split(':')[0]))
                                Found = True
                                break

    @staticmethod
    def create_patch(slither, patches, in_file, match_text, replace_text, modify_loc_start, modify_loc_end):
        in_file_str = slither.source_code[in_file]
        old_str_of_interest = in_file_str[modify_loc_start:modify_loc_end]
        old_str_of_interest_beyond_parameters = ')'.join(old_str_of_interest.split(')')[1:])
        s = old_str_of_interest_beyond_parameters.split('(')
        if len(s) == 1:
            account_for_return = 0
        else:
            account_for_return = 1
        old_str_of_interest_beyond_parameters_before_modifier_return = old_str_of_interest_beyond_parameters.split('(')[0]
        m = re.search("public", old_str_of_interest_beyond_parameters_before_modifier_return)
        if m is None:
            # No visibility specifier exists; public by default.
            (new_str_of_interest, _) = re.subn(" ", " external ", old_str_of_interest_beyond_parameters_before_modifier_return, 1)
            patches[in_file].append({
                "detector" : "external-function",
                "start" : modify_loc_start + len(old_str_of_interest.split(')')[0]) + 1,
                "end" : modify_loc_end - len('('.join(old_str_of_interest_beyond_parameters.split('(')[1:])) - account_for_return,
                "old_string" : old_str_of_interest_beyond_parameters_before_modifier_return,
                "new_string" : new_str_of_interest
            })
        else:
            (new_str_of_interest, _) = re.subn(match_text, replace_text, old_str_of_interest_beyond_parameters_before_modifier_return, 1)
            patches[in_file].append({
                "detector" : "external-function",
                "start" : modify_loc_start + len(old_str_of_interest.split(')')[0]) + 1 + m.span()[0],
                "end" : modify_loc_end - len('('.join(old_str_of_interest_beyond_parameters.split('(')[1:])) - account_for_return,
                "old_string" : old_str_of_interest_beyond_parameters_before_modifier_return,
                "new_string" : new_str_of_interest
            })

    @staticmethod
    def function_parameters_written(function):
        for node in function.nodes:
            if any (var.name == parameter.name for var in node.local_variables_written for parameter in function.parameters):
                return True
        return False
            
