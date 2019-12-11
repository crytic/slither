"""
    Check that the same pragma is used in all the files
"""

from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.formatters.attributes.constant_pragma import format


class ConstantPragma(AbstractDetector):
    """
    Check that the same pragma is used in all the files
    """

    ARGUMENT = 'pragma'
    HELP = 'If different pragma directives are used'
    IMPACT = DetectorClassification.INFORMATIONAL
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = 'https://github.com/crytic/slither/wiki/Detector-Documentation#different-pragma-directives-are-used'


    WIKI_TITLE = 'Different pragma directives are used'
    WIKI_DESCRIPTION = 'Detect if different Solidity versions are used.'
    WIKI_RECOMMENDATION = 'Use one Solidity version.'

    def _detect(self):
        results = []
        pragma = self.slither.pragma_directives
        versions = [p.version for p in pragma if p.is_solidity_version]
        versions = sorted(list(set(versions)))

        if len(versions) > 1:
            info = [f"Different versions of Solidity is used in {self.filename}:\n"]
            info += [f"\t- Version used: {[str(v) for v in versions]}\n"]

            for p in pragma:
                info += ["\t- ", p, "\n"]

            res = self.generate_result(info)

            results.append(res)

        return results

    @staticmethod
    def _format(slither, result):
        format(slither, result)
