import re

class FormatSolcVersion:

    # Indicates the recommended versions for replacement
    REPLACEMENT_VERSIONS = ["0.4.25", "0.5.3"]

    # group:
    # 0: ^ > >= < <= (optional)
    # 1: ' ' (optional)
    # 2: version number
    # 3: version number
    # 4: version number
    PATTERN = re.compile('(\^|>|>=|<|<=)?([ ]+)?(\d+)\.(\d+)\.(\d+)')

    @staticmethod
    def format(slither, patches, elements):
        for element in elements:
            solc_version_replace = FormatSolcVersion.determine_solc_version_replacement(element['expression'])
            FormatSolcVersion.create_patch(slither, patches, element['source_mapping']['filename'], solc_version_replace, element['source_mapping']['start'], element['source_mapping']['start'] + element['source_mapping']['length'])

    @staticmethod
    def determine_solc_version_replacement(used_solc_version):
        versions = FormatSolcVersion.PATTERN.findall(used_solc_version)
        if len(versions) == 1:
            version = versions[0]
            minor_version = '.'.join(version[2:])[2]
            if minor_version == '4':
                return "pragma solidity " + FormatSolcVersion.REPLACEMENT_VERSIONS[0] + ';'
            elif minor_version == '5':
                return "pragma solidity " + FormatSolcVersion.REPLACEMENT_VERSIONS[1] + ';'
            else:
                print("Unknown version!")
                sys.exit(-1)
        elif len(versions) == 2:
            version_left = versions[0]
            version_right = versions[1]
            minor_version_left = '.'.join(version_left[2:])[2]
            minor_version_right = '.'.join(version_right[2:])[2]
            if minor_version_right == '4':
                return "pragma solidity " + FormatSolcVersion.REPLACEMENT_VERSIONS[0] + ';'
            elif minor_version_right in ['5','6']:
                return "pragma solidity " + FormatSolcVersion.REPLACEMENT_VERSIONS[1] + ';'
            
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
