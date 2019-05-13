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
                        if contract.name == element['contract']['name'] and function.name == element['name']:
                            FormatConstantFunction.create_patch(slither, patches, element['source_mapping']['filename_absolute'], ["view","pure","constant"], "", int(function.parameters_src.split(':')[0]), int(function.returns_src.split(':')[0]))
                            Found = True

    @staticmethod
    def create_patch(slither, patches, in_file, match_text, replace_text, modify_loc_start, modify_loc_end):
        in_file_str = slither.source_code[in_file]
        old_str_of_interest = in_file_str[modify_loc_start:modify_loc_end]
        for match_text_item in match_text:
            (new_str_of_interest, num_repl) = re.subn(match_text_item, replace_text, old_str_of_interest, 1)
            if num_repl != 0:
                break
        if num_repl != 0:
            patches[in_file].append({
                "detector" : "constant-function",
                "start" : modify_loc_start,
                "end" : modify_loc_end,
                "old_string" : old_str_of_interest,
                "new_string" : new_str_of_interest
            })
        else:
            print("Error: No view/pure/constant specifier exists. Regex failed to remove specifier!")
            sys.exit(-1)
