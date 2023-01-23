from slither.core.declarations import Function
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.utils.code_complexity import compute_cyclomatic_complexity


class CyclomaticComplexity(AbstractDetector):
    """
    Detects functions with high (> 11) cyclomatic complexity.
    """

    ARGUMENT = "cyclomatic-complexity"
    HELP = "Detects functions with high (> 11) cyclomatic complexity"
    IMPACT = DetectorClassification.INFORMATIONAL
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = 'https://github.com/crytic/slither/wiki/Detector-Documentation#cyclomatic-complexity"'

    WIKI_TITLE = "Cyclomatic complexity detector"
    WIKI_DESCRIPTION = "Detects functions with high (> 11) cyclomatic complexity."
    WIKI_EXPLOIT_SCENARIO = ""
    WIKI_RECOMMENDATION = (
        "Reduce cyclomatic complexity by splitting the function into several smaller subroutines."
    )

    @staticmethod
    def _check_for_high_cc(high_cc_functions: list[(Function, int)], f: Function):
        cc = compute_cyclomatic_complexity(f)
        if cc > 11:
            high_cc_functions.append((f, cc))

    def _detect(self):
        results = []
        high_cc_functions = []

        for c in self.compilation_unit.contracts:
            for f in c.functions_declared:
                CyclomaticComplexity._check_for_high_cc(high_cc_functions, f)

        for f in self.compilation_unit.functions_top_level:
            CyclomaticComplexity._check_for_high_cc(high_cc_functions, f)

        for f, cc in high_cc_functions:
            info = [f, f" has a high cyclomatic complexity ({cc}).\n"]
            res = self.generate_result(info)
            results.append(res)
        return results
