import re
from slither.exceptions import SlitherException
from ..utils.patches import create_patch


class FormatPragma:

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
        versions_used = []
        for element in elements:
            versions_used.append(''.join(element['type_specific_fields']['directive'][1:]))
        solc_version_replace = FormatPragma.analyse_versions(versions_used)
        for element in elements:
            FormatPragma.create_patch(slither, patches, element['source_mapping']['filename_absolute'],
                                      element['source_mapping']['filename_relative'], solc_version_replace,
                                      element['source_mapping']['start'],
                                      element['source_mapping']['start'] + element['source_mapping']['length'])

    @staticmethod
    def analyse_versions(used_solc_versions):
        replace_solc_versions = list()
        for version in used_solc_versions:
            replace_solc_versions.append(FormatPragma.determine_solc_version_replacement(version))
        if not all(version == replace_solc_versions[0] for version in replace_solc_versions):
            raise SlitherException("Multiple incompatible versions!")
        else:
            return replace_solc_versions[0]

    @staticmethod
    def determine_solc_version_replacement(used_solc_version):
        versions = FormatPragma.PATTERN.findall(used_solc_version)
        if len(versions) == 1:
            version = versions[0]
            minor_version = '.'.join(version[2:])[2]
            if minor_version == '4':
                return "pragma solidity " + FormatPragma.REPLACEMENT_VERSIONS[0] + ';'
            elif minor_version == '5':
                return "pragma solidity " + FormatPragma.REPLACEMENT_VERSIONS[1] + ';'
            else:
                raise SlitherException("Unknown version!")
        elif len(versions) == 2:
            version_right = versions[1]
            minor_version_right = '.'.join(version_right[2:])[2]
            if minor_version_right == '4':
                return "pragma solidity " + FormatPragma.REPLACEMENT_VERSIONS[0] + ';'
            elif minor_version_right in ['5', '6']:
                return "pragma solidity " + FormatPragma.REPLACEMENT_VERSIONS[1] + ';'

    @staticmethod
    def create_patch(slither, patches, in_file, in_file_relative, pragma, modify_loc_start, modify_loc_end):
        in_file_str = slither.source_code[in_file].encode('utf-8')
        old_str_of_interest = in_file_str[modify_loc_start:modify_loc_end]
        create_patch(patches,
                     "pragma",
                     in_file_relative,
                     in_file,
                     int(modify_loc_start),
                     int(modify_loc_end),
                     old_str_of_interest.decode('utf-8'),
                     pragma)
