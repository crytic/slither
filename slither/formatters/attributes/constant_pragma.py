import re
from typing import Dict, List, Union

from slither.core.compilation_unit import SlitherCompilationUnit
from slither.formatters.exceptions import FormatImpossible
from slither.formatters.utils.patches import create_patch

# Indicates the recommended versions for replacement
REPLACEMENT_VERSIONS = ["^0.4.25", "^0.5.3"]

# pylint: disable=anomalous-backslash-in-string

# group:
# 0: ^ > >= < <= (optional)
# 1: ' ' (optional)
# 2: version number
# 3: version number
# 4: version number
PATTERN = re.compile(r"(\^|>|>=|<|<=)?([ ]+)?(\d+)\.(\d+)\.(\d+)")


def custom_format(slither: SlitherCompilationUnit, result: Dict) -> None:
    elements = result["elements"]
    versions_used: List[str] = []
    for element in elements:
        versions_used.append("".join(element["type_specific_fields"]["directive"][1:]))
    solc_version_replace = _analyse_versions(versions_used)
    for element in elements:
        _patch(
            slither,
            result,
            element["source_mapping"]["filename_absolute"],
            solc_version_replace,
            element["source_mapping"]["start"],
            element["source_mapping"]["start"] + element["source_mapping"]["length"],
        )


def _analyse_versions(used_solc_versions: List[str]) -> str:
    replace_solc_versions = []
    for version in used_solc_versions:
        replace_solc_versions.append(_determine_solc_version_replacement(version))
    if not all(version == replace_solc_versions[0] for version in replace_solc_versions):
        raise FormatImpossible("Multiple incompatible versions!")
    return replace_solc_versions[0]


def _determine_solc_version_replacement(used_solc_version: str) -> str:
    versions = PATTERN.findall(used_solc_version)
    if len(versions) == 1:
        version = versions[0]
        minor_version = ".".join(version[2:])[2]
        if minor_version == "4":
            return "pragma solidity " + REPLACEMENT_VERSIONS[0] + ";"
        if minor_version == "5":
            return "pragma solidity " + REPLACEMENT_VERSIONS[1] + ";"
        raise FormatImpossible("Unknown version!")
    if len(versions) == 2:
        version_right = versions[1]
        minor_version_right = ".".join(version_right[2:])[2]
        if minor_version_right == "4":
            # Replace with 0.4.25
            return "pragma solidity " + REPLACEMENT_VERSIONS[0] + ";"
        if minor_version_right in ["5", "6"]:
            # Replace with 0.5.3
            return "pragma solidity " + REPLACEMENT_VERSIONS[1] + ";"
    raise FormatImpossible("Unknown version!")


# pylint: disable=too-many-arguments
def _patch(
    slither: SlitherCompilationUnit,
    result: Dict,
    in_file: str,
    pragma: Union[str, bytes],
    modify_loc_start: int,
    modify_loc_end: int,
) -> None:
    in_file_str = slither.core.source_code[in_file].encode("utf8")
    old_str_of_interest = in_file_str[modify_loc_start:modify_loc_end]
    create_patch(
        result,
        in_file,
        int(modify_loc_start),
        int(modify_loc_end),
        old_str_of_interest,
        pragma,
    )
