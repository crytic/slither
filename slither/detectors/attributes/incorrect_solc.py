"""
Check if an incorrect version of solc is used
"""

import re

from slither.detectors.abstract_detector import (
    AbstractDetector,
    DetectorClassification,
    DETECTOR_INFO,
)
from slither.formatters.attributes.incorrect_solc import custom_format
from slither.utils.output import Output
from slither.utils.buggy_versions import bugs_by_version

# group:
# 0: ^ > >= < <= (optional)
# 1: ' ' (optional)
# 2: version number
# 3: version number
# 4: version number


PATTERN = re.compile(r"(\^|>|>=|<|<=)?([ ]+)?(\d+)\.(\d+)\.(\d+)")


class IncorrectSolc(AbstractDetector):
    """
    Check if an old version of solc is used
    """

    ARGUMENT = "solc-version"
    HELP = "Incorrect Solidity version"
    IMPACT = DetectorClassification.INFORMATIONAL
    CONFIDENCE = DetectorClassification.HIGH
    LANGUAGE = "solidity"
    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#incorrect-versions-of-solidity"

    WIKI_TITLE = "Incorrect versions of Solidity"

    # region wiki_description
    WIKI_DESCRIPTION = """
`solc` frequently releases new compiler versions. Using an old version prevents access to new Solidity security checks.
We also recommend avoiding complex `pragma` statement."""
    # endregion wiki_description

    # region wiki_recommendation
    WIKI_RECOMMENDATION = """
Deploy with a recent version of Solidity (at least 0.8.0) with no known severe issues.

Use a simple pragma version that allows any of these versions.
Consider using the latest version of Solidity for testing."""
    # endregion wiki_recommendation

    COMPLEX_PRAGMA_TXT = "is too complex"
    OLD_VERSION_TXT = (
        "is an outdated solc version. Use a more recent version (at least 0.8.0), if possible."
    )
    LESS_THAN_TXT = "uses lesser than"

    BUGGY_VERSION_TXT = (
        "contains known severe issues (https://solidity.readthedocs.io/en/latest/bugs.html)"
    )

    # Indicates the allowed versions. Must be formatted in increasing order.
    ALLOWED_VERSIONS = ["0.8.0"]

    def _check_version(self, version: tuple[str, str, str, str, str]) -> str | None:
        op = version[0]
        if op and op not in [">", ">=", "^"]:
            return self.LESS_THAN_TXT
        version_number = ".".join(version[2:])
        if version_number in bugs_by_version and len(bugs_by_version[version_number]):
            bugs = "\n".join([f"\t- {bug}" for bug in bugs_by_version[version_number]])
            return self.BUGGY_VERSION_TXT + f"\n{bugs}"
        return None

    def _check_pragma(self, version: str) -> str | None:
        versions = PATTERN.findall(version)
        if len(versions) == 1:
            version = versions[0]
            return self._check_version(version)
        if len(versions) == 2:
            version_left = versions[0]
            version_right = versions[1]
            # Only allow two elements if the second one is
            # <0.5.0 or <0.6.0
            if version_right not in [
                ("<", "", "0", "5", "0"),
                ("<", "", "0", "6", "0"),
                ("<", "", "0", "7", "0"),
            ]:
                return self.COMPLEX_PRAGMA_TXT
            return self._check_version(version_left)
        return self.COMPLEX_PRAGMA_TXT

    def _detect(self) -> list[Output]:
        """
        Detects pragma statements that allow for outdated solc versions.
        :return: Returns the relevant JSON data for the findings.
        """
        # Detect all version related pragmas and check if they are disallowed.
        results = []
        pragma = self.compilation_unit.pragma_directives
        disallowed_pragmas = {}

        for p in pragma:
            # Skip any pragma directives which do not refer to version
            if len(p.directive) < 1 or p.directive[0] != "solidity":
                continue

            reason = self._check_pragma(p.version)
            if reason is None:
                continue

            if p.version in disallowed_pragmas and reason in disallowed_pragmas[p.version]:
                disallowed_pragmas[p.version][reason].append(p)
            else:
                disallowed_pragmas[p.version] = {reason: [p]}

        # If we found any disallowed pragmas, we output our findings.
        if len(disallowed_pragmas.keys()):
            for p, reasons in disallowed_pragmas.items():
                info: DETECTOR_INFO = []
                for r, vers in reasons.items():
                    info += [f"Version constraint {p} {r}.\nIt is used by:\n"]
                    for ver in vers:
                        info += ["\t- ", ver, "\n"]

                json = self.generate_result(info)

                results.append(json)

        if list(map(int, self.compilation_unit.solc_version.split("."))) < list(
            map(int, self.ALLOWED_VERSIONS[-1].split("."))
        ):
            info = [
                "solc-",
                self.compilation_unit.solc_version,
                " ",
                self.OLD_VERSION_TXT,
                "\n",
            ]

            json = self.generate_result(info)

            # TODO: Once crytic-compile adds config file info, add a source mapping element pointing to
            #       the line in the config that specifies the problematic version of solc

            results.append(json)

        return results

    @staticmethod
    def _format(slither, result):
        custom_format(slither, result)
