"""
    Check if an incorrect version of solc is used
"""

import re
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.formatters.attributes.incorrect_solc import format

# group:
# 0: ^ > >= < <= (optional)
# 1: ' ' (optional)
# 2: version number
# 3: version number
# 4: version number

PATTERN = re.compile('(\^|>|>=|<|<=)?([ ]+)?(\d+)\.(\d+)\.(\d+)')


class IncorrectSolc(AbstractDetector):
    """
    Check if an old version of solc is used
    """

    ARGUMENT = 'solc-version'
    HELP = 'Incorrect Solidity version (< 0.4.24 or complex pragma)'
    IMPACT = DetectorClassification.INFORMATIONAL
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = 'https://github.com/crytic/slither/wiki/Detector-Documentation#incorrect-versions-of-solidity'

    WIKI_TITLE = 'Incorrect versions of Solidity'
    WIKI_DESCRIPTION = '''
Solc frequently releases new compiler versions. Using an old version prevents access to new Solidity security checks.
We recommend avoiding complex pragma statement.'''
    WIKI_RECOMMENDATION = '''
Use Solidity 0.4.25 or 0.5.3. Consider using the latest version of Solidity for testing the compilation, and a trusted version for deploying.'''

    COMPLEX_PRAGMA_TXT = "is too complex"
    OLD_VERSION_TXT = "allows old versions"
    LESS_THAN_TXT = "uses lesser than"

    TOO_RECENT_VERSION_TXT = "necessitates versions too recent to be trusted. Consider deploying with 0.5.3"
    BUGGY_VERSION_TXT = "is known to contain severe issue (https://solidity.readthedocs.io/en/v0.5.8/bugs.html)"

    # Indicates the allowed versions. Must be formatted in increasing order.
    ALLOWED_VERSIONS = ["0.4.25", "0.4.26", "0.5.11"]

    # Indicates the versions that should not be used.
    BUGGY_VERSIONS = ["0.4.22", "^0.4.22",
                      "0.5.5", "^0.5.5",
                      "0.5.6", "^0.5.6",
                      "0.5.14", "^0.5.14"]

    def _check_version(self, version):
        op = version[0]
        if op and op not in ['>', '>=', '^']:
            return self.LESS_THAN_TXT
        version_number = '.'.join(version[2:])
        if version_number not in self.ALLOWED_VERSIONS:
            if list(map(int, version[2:])) > list(map(int, self.ALLOWED_VERSIONS[-1].split('.'))):
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
        elif len(versions) == 2:
            version_left = versions[0]
            version_right = versions[1]
            # Only allow two elements if the second one is
            # <0.5.0 or <0.6.0
            if version_right not in [('<', '', '0', '5', '0'), ('<', '', '0', '6', '0'), ('<', '', '0', '7', '0')]:
                return self.COMPLEX_PRAGMA_TXT
            return self._check_version(version_left)
        else:
            return self.COMPLEX_PRAGMA_TXT

    def _detect(self):
        """
        Detects pragma statements that allow for outdated solc versions.
        :return: Returns the relevant JSON data for the findings.
        """
        # Detect all version related pragmas and check if they are disallowed.
        results = []
        pragma = self.slither.pragma_directives
        disallowed_pragmas = []
        detected_version = False
        for p in pragma:
            # Skip any pragma directives which do not refer to version
            if len(p.directive) < 1 or p.directive[0] != "solidity":
                continue

            # This is version, so we test if this is disallowed.
            detected_version = True
            reason = self._check_pragma(p.version)
            if reason:
                disallowed_pragmas.append((reason, p))

        # If we found any disallowed pragmas, we output our findings.
        if disallowed_pragmas:
            for (reason, p) in disallowed_pragmas:
                info = ["Pragma version", p, f" {reason}\n"]

                json = self.generate_result(info)

                results.append(json)

        return results

    @staticmethod
    def _format(slither, result):
        format(slither, result)
