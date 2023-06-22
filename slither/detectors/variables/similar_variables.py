"""
Check for state variables too similar
Do not check contract inheritance
"""
import difflib
from typing import List, Set, Tuple

from slither.core.declarations.contract import Contract
from slither.core.variables.local_variable import LocalVariable
from slither.detectors.abstract_detector import (
    AbstractDetector,
    DetectorClassification,
    DETECTOR_INFO,
)
from slither.utils.output import Output


class SimilarVarsDetection(AbstractDetector):
    """
    Variable similar detector
    """

    ARGUMENT = "similar-names"
    HELP = "Variable names are too similar"
    IMPACT = DetectorClassification.INFORMATIONAL
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = (
        "https://github.com/crytic/slither/wiki/Detector-Documentation#variable-names-too-similar"
    )

    WIKI_TITLE = "Variable names too similar"
    WIKI_DESCRIPTION = "Detect variables with names that are too similar."
    WIKI_EXPLOIT_SCENARIO = "Bob uses several variables with similar names. As a result, his code is difficult to review."
    WIKI_RECOMMENDATION = "Prevent variables from having similar names."

    @staticmethod
    def similar(seq1: str, seq2: str) -> bool:
        """Test the name similarity

        Two name are similar if difflib.SequenceMatcher on the lowercase
        version of the name is greater than 0.90
        See: https://docs.python.org/2/library/difflib.html
        Args:
            seq1 (str): first name
            seq2 (str): second name
        Returns:
            bool: true if names are similar
        """
        val = difflib.SequenceMatcher(a=seq1, b=seq2).ratio()
        ret = val > 0.90
        return ret

    @staticmethod
    def detect_sim(contract: Contract) -> Set[Tuple[LocalVariable, LocalVariable]]:
        """Detect variables with similar name

        Returns:
            bool: true if variables have similar name
        """
        all_var = [x.variables for x in contract.functions]
        all_var = [x for l in all_var for x in l]

        contract_var = contract.variables

        all_var = list(set(all_var + contract_var))

        ret = set()
        # pylint: disable=consider-using-enumerate
        for i in range(len(all_var)):
            v1 = all_var[i]
            _v1_name_lower = v1.name.lower()
            for j in range(i, len(all_var)):
                v2 = all_var[j]
                if len(v1.name) != len(v2.name):
                    continue
                _v2_name_lower = v2.name.lower()
                if _v1_name_lower != _v2_name_lower:
                    if SimilarVarsDetection.similar(_v1_name_lower, _v2_name_lower):
                        ret.add((v1, v2))

        return ret

    def _detect(self) -> List[Output]:
        """Detect similar variables name

        Returns:
            list: {'vuln', 'filename,'contract','vars'}
        """
        results = []
        for c in self.contracts:
            allVars = self.detect_sim(c)
            if allVars:
                for (v1, v2) in sorted(allVars, key=lambda x: (x[0].name, x[1].name)):
                    v_left = v1 if v1.name < v2.name else v2
                    v_right = v2 if v_left == v1 else v1
                    info: DETECTOR_INFO = [
                        "Variable ",
                        v_left,
                        " is too similar to ",
                        v_right,
                        "\n",
                    ]
                    json = self.generate_result(info)
                    results.append(json)
        return results
