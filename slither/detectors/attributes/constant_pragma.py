"""
    Check that the same pragma is used in all the files
"""

from slither.detectors.abstractDetector import AbstractDetector
from slither.detectors.detectorClassification import DetectorClassification

class ConstantPragma(AbstractDetector):
    """
    Check that the same pragma is used in all the files
    """

    ARGUMENT = 'pragma'
    HELP = 'Different pragma directives used'
    CLASSIFICATION = DetectorClassification.CODE_QUALITY


    def detect(self):
        """
        """

        results = []
        pragma = self.slither.pragma_directives
        pragma = [''.join(p[1:]) for p in pragma]
        pragma = list(set(pragma))
        if len(pragma) > 1:
            info = "Different version of Solidity used in {}: {}".format(self.filename, pragma)
            self.log(info)

            results.append({'vuln':'ConstantPragma', 'pragma': pragma})

        return results
