class FormatSolcVersion:

    @staticmethod
    def format(slither, patches, elements):
        # To-do: Determine which solc version to replace with
        # If < 0.4.24 replace with 0.4.25?
        # If > 0.5.0 replace with the latest 0.5.x?
        solc_version_replace = "pragma solidity ^0.4.25;"
        for element in elements:
            FormatSolcVersion.create_patch(slither, patches, element['source_mapping']['filename'], solc_version_replace, element['source_mapping']['start'], element['source_mapping']['start'] + element['source_mapping']['length'])

    @staticmethod
    def create_patch(slither, patches, in_file, solc_version, modify_loc_start, modify_loc_end):
        in_file_str = slither.source_code[in_file]
        old_str_of_interest = in_file_str[modify_loc_start:modify_loc_end]
        patches[in_file].append({
            "detector" : "solc-version",
	    "start" : modify_loc_start,
	    "end" : modify_loc_end,
	    "old_string" : old_str_of_interest,
	    "new_string" : solc_version
        })
