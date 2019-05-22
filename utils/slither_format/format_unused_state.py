class FormatUnusedState:

    @staticmethod
    def format(slither, patches, elements):
        for element in elements:
            if element['type'] == "variable":
                FormatUnusedState.create_patch(slither, patches, element['source_mapping']['filename_absolute'], element['source_mapping']['start'])

    @staticmethod
    def create_patch(slither, patches, in_file, modify_loc_start):
        in_file_str = slither.source_code[in_file].encode('utf-8')
        old_str_of_interest = in_file_str[modify_loc_start:]
        patches[in_file].append({
            "detector" : "unused-state",
            "start" : modify_loc_start,
            "end" : modify_loc_start + len(old_str_of_interest.decode('utf-8').partition(';')[0]) + 1,
            "old_string" : old_str_of_interest.decode('utf-8').partition(';')[0] + old_str_of_interest.decode('utf-8').partition(';')[1],
            "new_string" : ""
        })

