class FormatPragma:

    @staticmethod
    def format(slither, patches, elements):
        versions_used = []
        for element in elements:
            versions_used.append(element['expression'])
            # To-do Determine which version to replace with
            # The more recent of the two? What if they are the older deprecated versions? Replace it with the latest?
            # Impact of upgrading and compatibility? Cannot upgrade across breaking versions e.g. 0.4.x to 0.5.x.
        solc_version_replace = "^0.4.25"
        pragma = "pragma solidity " + solc_version_replace + ";"
        for element in elements:
            FormatPragma.create_patch(slither, patches, element['source_mapping']['filename'], pragma, element['source_mapping']['start'], element['source_mapping']['start'] + element['source_mapping']['length'])

    @staticmethod
    def create_patch(slither, patches, in_file, pragma, modify_loc_start, modify_loc_end):
        in_file_str = slither.source_code[in_file]
        old_str_of_interest = in_file_str[modify_loc_start:modify_loc_end]
        patches[in_file].append({
            "detector" : "pragma",
	    "start" : modify_loc_start,
	    "end" : modify_loc_end,
	    "old_string" : old_str_of_interest,
	    "new_string" : pragma
        })
