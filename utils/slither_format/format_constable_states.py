import re

class FormatConstableStates:

    @staticmethod
    def format(slither, patches, elements):
        for element in elements:
            FormatConstableStates.create_patch(slither, patches, element['source_mapping']['filename'], element['name'], "constant " + element['name'], element['source_mapping']['start'], element['source_mapping']['start'] + element['source_mapping']['length'])

    @staticmethod
    def create_patch(slither, patches, _in_file, _match_text, _replace_text, _modify_loc_start, _modify_loc_end):
        in_file_str = slither.source_code[_in_file]
        old_str_of_interest = in_file_str[_modify_loc_start:_modify_loc_end]
        (new_str_of_interest, num_repl) = re.subn(_match_text, _replace_text, old_str_of_interest, 1)
        if num_repl != 0:
            patches[_in_file].append({
                "detector" : "constable-states",
                "start" : _modify_loc_start,
                "end" : _modify_loc_start + len(new_str_of_interest),
                "old_string" : old_str_of_interest,
                "new_string" : new_str_of_interest
            })
        else:
            print("Error: State variable not found?!")
            sys.exit(-1)
