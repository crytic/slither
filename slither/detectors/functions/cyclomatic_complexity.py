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

    def _detect(self):
        results = []

        for f in self.compilation_unit.functions:
            cc = compute_cyclomatic_complexity(f)
            if cc > 11:
                info = (
                    "Function "
                    + f.name
                    + " defined at "
                    + str(f.source_mapping)
                    + " has high cyclomatic complexity ("
                    + str(cc)
                    + "). Consider splitting it into several smaller subroutines.\n"
                )
                res = self.generate_result(info)
                results.append(res)
        return results
