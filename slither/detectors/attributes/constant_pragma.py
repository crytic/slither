"""
    Check that the same pragma is used in all the files
"""
from typing import List, Dict

from slither.core.compilation_unit import SlitherCompilationUnit
from slither.detectors.abstract_detector import (
    AbstractDetector,
    DetectorClassification,
    DETECTOR_INFO,
)
from slither.formatters.attributes.constant_pragma import custom_format
from slither.utils.output import Output


class ConstantPragma(AbstractDetector):
    """
    Check that the same pragma is used in all the files
    """

    ARGUMENT = "pragma"
    HELP = "If different pragma directives are used"
    IMPACT = DetectorClassification.INFORMATIONAL
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#different-pragma-directives-are-used"

    WIKI_TITLE = "Different pragma directives are used"
    WIKI_DESCRIPTION = "Detect whether different Solidity versions are used."
    WIKI_RECOMMENDATION = "Use one Solidity version."

    def _detect(self) -> List[Output]:
        results = []
        pragma = self.compilation_unit.pragma_directives
        versions = [p.version for p in pragma if p.is_solidity_version]
        versions = sorted(list(set(versions)))

        if len(versions) > 1:
            info: DETECTOR_INFO = ["Different versions of Solidity are used:\n"]
            info += [f"\t- Version used: {[str(v) for v in versions]}\n"]

            for p in sorted(pragma, key=lambda x: x.version):
                info += ["\t- ", p, "\n"]

            res = self.generate_result(info)

            results.append(res)

        return results

    @staticmethod
    def _format(slither: SlitherCompilationUnit, result: Dict) -> None:
        custom_format(slither, result)
