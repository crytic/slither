from slither.core.declarations import Function
from slither.detectors.abstract_detector import (
    AbstractDetector,
    DetectorClassification,
    DETECTOR_INFO,
)
from slither.utils.code_complexity import compute_cyclomatic_complexity
from slither.utils.output import Output


def _check_for_high_cc(
    high_cc_functions: list[tuple[Function, int]], f: Function, threshold: int
) -> None:
    cc = compute_cyclomatic_complexity(f)
    if cc > threshold:
        high_cc_functions.append((f, cc))


class CyclomaticComplexity(AbstractDetector):
    """
    Detects functions above the configured cyclomatic-complexity threshold.
    """

    ARGUMENT = "cyclomatic-complexity"
    HELP = "Detects functions above the configured cyclomatic-complexity threshold (default: 11)"
    IMPACT = DetectorClassification.INFORMATIONAL
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#cyclomatic-complexity"

    WIKI_TITLE = "Cyclomatic complexity"
    WIKI_DESCRIPTION = "Detects functions above the configured cyclomatic-complexity threshold (default: 11)."
    WIKI_EXPLOIT_SCENARIO = ""
    WIKI_RECOMMENDATION = (
        "Reduce cyclomatic complexity by splitting the function into several smaller subroutines."
    )

    def _detect(self) -> list[Output]:
        results = []
        high_cc_functions: list[tuple[Function, int]] = []
        threshold = getattr(self.slither, "cyclomatic_complexity_threshold", 11)

        f: Function
        for c in self.compilation_unit.contracts:
            for f in c.functions_declared:
                _check_for_high_cc(high_cc_functions, f, threshold)

        for f in self.compilation_unit.functions_top_level:
            _check_for_high_cc(high_cc_functions, f)

        for f, cc in high_cc_functions:
            info: DETECTOR_INFO = [f, f" has a high cyclomatic complexity ({cc}).\n"]
            res = self.generate_result(info)
            results.append(res)
        return results
