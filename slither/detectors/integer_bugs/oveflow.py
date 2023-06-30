from typing import List

from slither.detectors.abstract_detector import (
    AbstractDetector,
    DetectorClassification,
    DETECTOR_INFO,
)
from slither.utils.output import Output


class Overflow(AbstractDetector):
    """
    Detect function named backdoor
    """

    ARGUMENT = "overflow"
    HELP = "Detect operation include +/-/*// which has integer in expression"
    IMPACT = DetectorClassification.HIGH
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = "https://swcregistry.io/docs/SWC-101"
    WIKI_TITLE = "Integer overflow"
    WIKI_DESCRIPTION = "Detect operation include +/-/*// which has integer in expression"
    WIKI_EXPLOIT_SCENARIO = ".."
    WIKI_RECOMMENDATION = "Make sure the expression will never overflow or use SafeMath util"

    def _detect(self) -> List[Output]:

        # Output Result
        results = []
        operators = ['+', '-', '*', '%', '**', ]

        for contract in self.compilation_unit.contracts_derived:
            for function in contract.functions:
                for node in function.nodes:
                    # Find operator and integer in expression
                    if node.expression:
                        if any(op in str(node.expression) for op in operators):
                            if any('int' in str(variable.type) for variable in node.variables_read):
                                # Info to be printed
                                info: DETECTOR_INFO = ["Expression:\n", node, " may overflow.\n"]

                                # Add the result in result
                                res = self.generate_result(info)

                                results.append(res)
        return results
