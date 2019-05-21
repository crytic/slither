import re

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
                            FormatConstantFunction.create_patch(slither, patches, element['source_mapping']['filename_absolute'], ["view","pure","constant"], "", int(function.parameters_src.source_mapping['start']), int(function.returns_src.source_mapping['start']))
                            Found = True

    @staticmethod
    def create_patch(slither, patches, in_file, match_text, replace_text, modify_loc_start, modify_loc_end):
        in_file_str = slither.source_code[in_file]
        old_str_of_interest = in_file_str[modify_loc_start:modify_loc_end]
        m = re.search("(view|pure|constant)", old_str_of_interest)
        if m:
            patches[in_file].append({
                "detector" : "constant-function",
                "start" : modify_loc_start + m.span()[0],
                "end" : modify_loc_start + m.span()[1],
                "old_string" : m.groups(0)[0],
                "new_string" : replace_text
            })
        else:
            print("Error: No view/pure/constant specifier exists. Regex failed to remove specifier!")
            sys.exit(-1)
