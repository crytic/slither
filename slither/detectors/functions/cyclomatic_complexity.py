from typing import List, Tuple

from slither.core.declarations import Function
from slither.detectors.abstract_detector import (
    AbstractDetector,
    DetectorClassification,
    DETECTOR_INFO,
)
from slither.utils.code_complexity import compute_cyclomatic_complexity
from slither.utils.output import Output


def _check_for_high_cc(high_cc_functions: List[Tuple[Function, int]], f: Function) -> None:
    cc = compute_cyclomatic_complexity(f)
    if cc > 11:
        high_cc_functions.append((f, cc))


class CyclomaticComplexity(AbstractDetector):
    """
    Detects functions with high (> 11) cyclomatic complexity.
    """

    ARGUMENT = "cyclomatic-complexity"
    HELP = "Detects functions with high (> 11) cyclomatic complexity"
    IMPACT = DetectorClassification.INFORMATIONAL
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#cyclomatic-complexity"

    WIKI_TITLE = "Cyclomatic complexity"
    WIKI_DESCRIPTION = "Detects functions with high (> 11) cyclomatic complexity."
    WIKI_EXPLOIT_SCENARIO = ""
    WIKI_RECOMMENDATION = (
        "Reduce cyclomatic complexity by splitting the function into several smaller subroutines."
    )

    def _detect(self) -> List[Output]:
        results = []
        high_cc_functions: List[Tuple[Function, int]] = []

        f: Function
        for c in self.compilation_unit.contracts:
            for f in c.functions_declared:
                _check_for_high_cc(high_cc_functions, f)

        for f in self.compilation_unit.functions_top_level:
            _check_for_high_cc(high_cc_functions, f)

        for f, cc in high_cc_functions:
            info: DETECTOR_INFO = [f, f" has a high cyclomatic complexity ({cc}).\n"]
            res = self.generate_result(info)
            results.append(res)
        return results
