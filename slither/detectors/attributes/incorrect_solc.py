"""
    Check if an incorrect version of solc is used
"""

from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
import re

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

    WIKI = 'https://github.com/trailofbits/slither/wiki/Vulnerabilities-Description#incorrect-version-of-solidity'

    WIKI_TITLE = 'Incorrect versions of Solidity'
    WIKI_DESCRIPTION = '''
Solc frequently releases new compiler versions. Using an old version prevent access to new Solidity security checks.
We recommend avoiding complex pragma statement.'''
    WIKI_RECOMMENDATION = 'Use Solidity 0.4.25 or 0.5.2.'

    COMPLEX_PRAGMA = "is has a complex pragma"
    OLD_VERSION = "it allows old versions"
    LESS_THAN = "it uses lesser than"

    # Indicates the allowed versions.
    ALLOWED_VERSIONS = ["0.4.24", "0.4.25", "0.5.2", "0.5.3"]

    def _check_version(self, version):
        op = version[0]
        if op and not op in ['>', '>=', '^']:
            return self.LESS_THAN
        version_number = '.'.join(version[2:])
        if version_number not in self.ALLOWED_VERSIONS:
            return self.OLD_VERSION
        return None

    def _check_pragma(self, version):
        versions = PATTERN.findall(version)
        if len(versions) == 1:
            version = versions[0]
            return self._check_version(version)
        elif len(versions) == 2:
            version_left = versions[0]
            version_right = versions[1]
            # Only allow two elements if the second one is
            # <0.5.0 or <0.6.0
            if version_right not in [('<', '', '0', '5', '0'), ('<', '', '0', '6', '0')]:
                return self.COMPLEX_PRAGMA
            return self._check_version(version_left)
        else:
            return self.COMPLEX_PRAGMA
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
            info = "Detected issues with version pragma in {}:\n".format(self.filename)
            for (reason, p) in disallowed_pragmas:
                info += "\t- {} ({}): {}\n".format(p, p.source_mapping_str, reason)

            json = self.generate_json_result(info)

            # follow the same format than add_nodes_to_json
            json['elements'] = [{'type': 'expression',
                                 'expression': p.version,
                                 'source_mapping': p.source_mapping} for (reason, p) in disallowed_pragmas]
            results.append(json)

        return results
