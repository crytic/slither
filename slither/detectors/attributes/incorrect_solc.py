"""
    Check if an incorrect version of solc is used
"""

import re
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.formatters.attributes.incorrect_solc import custom_format

# group:
# 0: ^ > >= < <= (optional)
# 1: ' ' (optional)
# 2: version number
# 3: version number
# 4: version number

# pylint: disable=anomalous-backslash-in-string
PATTERN = re.compile(r"(\^|>|>=|<|<=)?([ ]+)?(\d+)\.(\d+)\.(\d+)")


class IncorrectSolc(AbstractDetector):
    """
    Check if an old version of solc is used
    """

    ARGUMENT = "solc-version"
    HELP = "Incorrect Solidity version"
    IMPACT = DetectorClassification.INFORMATIONAL
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#incorrect-versions-of-solidity"

    WIKI_TITLE = "Incorrect versions of Solidity"

    # region wiki_description
    WIKI_DESCRIPTION = """
`solc` frequently releases new compiler versions. Using an old version prevents access to new Solidity security checks.
We also recommend avoiding complex `pragma` statement."""
    # endregion wiki_description

    # region wiki_recommendation
    WIKI_RECOMMENDATION = """
Deploy with any of the following Solidity versions:
- 0.5.16 - 0.5.17
- 0.6.11 - 0.6.12
- 0.7.5 - 0.7.6
- 0.8.16

The recommendations take into account:
- Risks related to recent releases
- Risks of complex code generation changes
- Risks of new language features
- Risks of known bugs

Use a simple pragma version that allows any of these versions.
Consider using the latest version of Solidity for testing."""
    # endregion wiki_recommendation

    COMPLEX_PRAGMA_TXT = "is too complex"
    OLD_VERSION_TXT = "allows old versions"
    LESS_THAN_TXT = "uses lesser than"

    TOO_RECENT_VERSION_TXT = "necessitates a version too recent to be trusted. Consider deploying with 0.6.12/0.7.6/0.8.7"
    BUGGY_VERSION_TXT = (
        "is known to contain severe issues (https://solidity.readthedocs.io/en/latest/bugs.html)"
    )

    # Indicates the allowed versions. Must be formatted in increasing order.
    ALLOWED_VERSIONS = [
        "0.5.16",
        "0.5.17",
        "0.6.11",
        "0.6.12",
        "0.7.5",
        "0.7.6",
        "0.8.16"
    ]

    # Indicates the versions that should not be used.
    BUGGY_VERSIONS = [
        "0.4.22",
        "^0.4.22",
        "0.5.5",
        "^0.5.5",
        "0.5.6",
        "^0.5.6",
        "0.5.14",
        "^0.5.14",
        "0.6.9",
        "^0.6.9",
        "0.8.8",
        "^0.8.8",
    ]

    def _check_version(self, version):
        op = version[0]
        if op and op not in [">", ">=", "^"]:
            return self.LESS_THAN_TXT
        version_number = ".".join(version[2:])
        if version_number in self.BUGGY_VERSIONS:
            return self.BUGGY_VERSION_TXT
        if version_number not in self.ALLOWED_VERSIONS:
            if list(map(int, version[2:])) > list(map(int, self.ALLOWED_VERSIONS[-1].split("."))):
                return self.TOO_RECENT_VERSION_TXT
            return self.OLD_VERSION_TXT
        return None

    def _check_pragma(self, version):
        if version in self.BUGGY_VERSIONS:
            return self.BUGGY_VERSION_TXT
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

    def _detect(self):
        """
        Detects pragma statements that allow for outdated solc versions.
        :return: Returns the relevant JSON data for the findings.
        """
        # Detect all version related pragmas and check if they are disallowed.
        results = []
        pragma = self.compilation_unit.pragma_directives
        disallowed_pragmas = []

        for p in pragma:
            # Skip any pragma directives which do not refer to version
            if len(p.directive) < 1 or p.directive[0] != "solidity":
                continue

            # This is version, so we test if this is disallowed.
            reason = self._check_pragma(p.version)
            if reason:
                disallowed_pragmas.append((reason, p))

        # If we found any disallowed pragmas, we output our findings.
        if disallowed_pragmas:
            for (reason, p) in disallowed_pragmas:
                info = ["Pragma version", p, f" {reason}\n"]

                json = self.generate_result(info)

                results.append(json)

        if self.compilation_unit.solc_version not in self.ALLOWED_VERSIONS:

            if self.compilation_unit.solc_version in self.BUGGY_VERSIONS:
                info = [
                    "solc-",
                    self.compilation_unit.solc_version,
                    " ",
                    self.BUGGY_VERSION_TXT,
                ]
            else:
                info = [
                    "solc-",
                    self.compilation_unit.solc_version,
                    " is not recommended for deployment\n",
                ]

            json = self.generate_result(info)

            # TODO: Once crytic-compile adds config file info, add a source mapping element pointing to
            #       the line in the config that specifies the problematic version of solc

            results.append(json)

        return results

    @staticmethod
    def _format(slither, result):
        custom_format(slither, result)
