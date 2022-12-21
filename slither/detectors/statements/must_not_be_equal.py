"""
Module suspecting they must be not equal.

"""

from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.slithir.operations import Binary, BinaryType
from itertools import permutations


class MustBeNotEqual(AbstractDetector):
    """
    Suspect they must be not equal
    """

    ARGUMENT = "must-be-not-equal"
    HELP = "Missing condition checking if they are equal"
    IMPACT = DetectorClassification.INFORMATIONAL
    CONFIDENCE = DetectorClassification.LOW

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#must-be-not-equal"
    WIKI_TITLE = "MUST_BE_NOT_EQUAL"
    WIKI_DESCRIPTION = "MUST_BE_NOT_EQUAL"
    WIKI_EXPLOIT_SCENARIO = """
https://rekt.news/monox-rekt/
https://etherscan.io/address/0x66e7d7839333f502df355f5bd87aea24bac2ee63#code#F1#L807
"""
    WIKI_RECOMMENDATION = "Suspect whether variables of address type must be not equal"

    def _detect(self):
        results = []
        likely = [
            ["from", "to"],
            ["out", "in"],
            ["send", "rec"],
            ["sour", "dest"],
        ]  # heuristic key point. anyone can update.

        for contract in self.compilation_unit.contracts:
            for function in contract.functions:
                if function._pure == True or function._view == True:
                    continue

                pairs = list(permutations(function._parameters, 2))
                check_flag = 0

                for pair in pairs:

                    if str(pair[0].type) == "address" and str(pair[1].type) == "address":
                        for cand in likely:
                            find_flag = 0

                            if cand[0] in pair[0].name.lower() and cand[1] in pair[1].name.lower():
                                find_flag = 1
                            if cand[0] in pair[1].name.lower() and cand[1] in pair[0].name.lower():
                                find_flag = 1

                            if find_flag == 1:
                                for node in function.nodes:
                                    for ir in node.irs:
                                        if isinstance(ir, Binary):
                                            # heuristic: parameter -> temporary variable will not occur.
                                            if ir.type is BinaryType.NOT_EQUAL:
                                                if (
                                                    ir.variable_left == pair[0]
                                                    and ir.variable_right == pair[1]
                                                ):
                                                    check_flag = 1
                                                if (
                                                    ir.variable_right == pair[1]
                                                    and ir.variable_right == pair[0]
                                                ):
                                                    check_flag = 1
                            if find_flag == 1 and check_flag == 0:
                                info = ["Must-be-not-equal found in ", function, "\n"]
                                res = self.generate_result(info)
                                results.append(res)

        return results
