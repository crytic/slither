"""
    Check that the same pragma is used in all the files
"""
from collections import OrderedDict
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
        pragma_directives_by_version = OrderedDict()
        for pragma in self.compilation_unit.pragma_directives:
            if pragma.is_solidity_version:
                if pragma.version not in pragma_directives_by_version:
                    pragma_directives_by_version[pragma.version] = [pragma]
                else:
                    pragma_directives_by_version[pragma.version].append(pragma)

        versions = list(pragma_directives_by_version.keys())
        if len(versions) > 1:
            info: DETECTOR_INFO = [f"{len(versions)} different versions of Solidity are used:\n"]

            for version in versions:
                pragmas = pragma_directives_by_version[version]
                info += [f"\t- Version constraint {version} is used by:\n"]
                for pragma in pragmas:
                    info += ["\t\t-", pragma, "\n"]

            res = self.generate_result(info)

            results.append(res)

        return results

    @staticmethod
    def _format(slither: SlitherCompilationUnit, result: Dict) -> None:
        custom_format(slither, result)
