"""
    Check if an old version of solc is used
    Solidity >= 0.4.23 should be used
"""

from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification


class OldSolc(AbstractDetector):
    """
    Check if an old version of solc is used
    """

    ARGUMENT = 'solc-version'
    HELP = 'Old versions of Solidity (< 0.4.23)'
    IMPACT = DetectorClassification.INFORMATIONAL
    CONFIDENCE = DetectorClassification.HIGH

    def detect(self):
        results = []
        pragma = self.slither.pragma_directives
        versions = [p.version for p in pragma]
        versions = [p.replace('solidity', '').replace('^', '') for p in versions]
        versions = sorted(list(set(versions)))
        old_pragma = [p for p in versions if p not in ['0.4.23', '0.4.24']]

        if old_pragma:
            info = "Old version of Solidity used in {}: {}".format(self.filename, old_pragma)
            self.log(info)

            source = [p.source_mapping for p in pragma]
            results.append({'vuln': 'OldPragma',
                            'pragma': old_pragma,
                            'sourceMapping': source})

        return results
