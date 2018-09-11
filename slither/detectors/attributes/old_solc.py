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
    HELP = 'an old version of Solidity used (<0.4.23)'
    CLASSIFICATION = DetectorClassification.CODE_QUALITY

    def detect(self):
        results = []
        pragma = self.slither.pragma_directives
        pragma = [''.join(p[1:]) for p in pragma]
        pragma = [p.replace('solidity', '').replace('^', '') for p in pragma]
        pragma = list(set(pragma))
        old_pragma = [p for p in pragma if p not in ['0.4.23', '0.4.24']]

        if old_pragma:
            info = "Old version of Solidity used in {}: {}".format(self.filename, old_pragma)
            self.log(info)

            results.append({'vuln': 'OldPragma', 'pragma': old_pragma})

        return results
