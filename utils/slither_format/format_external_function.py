import re

class FormatExternalFunction:

    @staticmethod
    def format (slither, patches, elements):
        for element in elements:
            Found = False
            for contract in slither.contracts_derived:
                if not Found and contract.name == element['contract']['name']:
                    for function in contract.functions:
                        if function.name == element['name']:
                            FormatExternalFunction.create_patch(slither, patches, element['source_mapping']['filename'], "public", "external", int(function.parameters_src.split(':')[0]), int(function.returns_src.split(':')[0]))
                            Found = True
                            break

    @staticmethod
    def create_patch(slither, patches, _in_file, _match_text, _replace_text, _modify_loc_start, _modify_loc_end):
        in_file_str = slither.source_code[_in_file]
        old_str_of_interest = in_file_str[_modify_loc_start:_modify_loc_end]
        (new_str_of_interest, num_repl) = re.subn(_match_text, _replace_text, old_str_of_interest, 1)
        if num_repl == 0:
            # No visibility specifier exists; public by default.
            (new_str_of_interest, num_repl) = re.subn("\)", ") extern", old_str_of_interest, 1)
        if num_repl != 0:
            patches[_in_file].append({
                "detector" : "external-function",
                "start" : _modify_loc_start,
                "end" : _modify_loc_start + len(new_str_of_interest),
                "old_string" : old_str_of_interest,
                "new_string" : new_str_of_interest
            })
        else:
            print("Error: No public visibility specifier exists. Regex failed to add extern specifier!")
            sys.exit(-1)

