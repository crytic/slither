import re
from ..exceptions import FormatImpossible
from ..utils.patches import create_patch


# Indicates the recommended versions for replacement
REPLACEMENT_VERSIONS = ["^0.4.25", "^0.5.3"]

# group:
# 0: ^ > >= < <= (optional)
# 1: ' ' (optional)
# 2: version number
# 3: version number
# 4: version number
PATTERN = re.compile('(\^|>|>=|<|<=)?([ ]+)?(\d+)\.(\d+)\.(\d+)')

def format(slither, result):
    elements = result['elements']
    for element in elements:
        solc_version_replace = _determine_solc_version_replacement(
            ''.join(element['type_specific_fields']['directive'][1:]))

        _patch(slither, result, element['source_mapping']['filename_absolute'], solc_version_replace,
               element['source_mapping']['start'], element['source_mapping']['start'] +
               element['source_mapping']['length'])

def _determine_solc_version_replacement(used_solc_version):
    versions = PATTERN.findall(used_solc_version)
    if len(versions) == 1:
        version = versions[0]
        minor_version = '.'.join(version[2:])[2]
        if minor_version == '4':
            # Replace with 0.4.25
            return "pragma solidity " + REPLACEMENT_VERSIONS[0] + ';'
        elif minor_version == '5':
            # Replace with 0.5.3
            return "pragma solidity " + REPLACEMENT_VERSIONS[1] + ';'
        else:
            raise FormatImpossible(f"Unknown version {versions}")
    elif len(versions) == 2:
        version_right = versions[1]
        minor_version_right = '.'.join(version_right[2:])[2]
        if minor_version_right == '4':
            # Replace with 0.4.25
            return "pragma solidity " + REPLACEMENT_VERSIONS[0] + ';'
        elif minor_version_right in ['5','6']:
            # Replace with 0.5.3
            return "pragma solidity " + REPLACEMENT_VERSIONS[1] + ';'


def _patch(slither, result, in_file, solc_version, modify_loc_start, modify_loc_end):
    in_file_str = slither.source_code[in_file].encode('utf-8')
    old_str_of_interest = in_file_str[modify_loc_start:modify_loc_end]
    create_patch(result,
                 in_file,
                 int(modify_loc_start),
                 int(modify_loc_end),
                 old_str_of_interest.decode('utf-8'),
                 solc_version)
