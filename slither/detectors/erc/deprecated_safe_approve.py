"""
Module detecting deprecated safeApprove usage
"""

from slither.core.declarations.function import Function
from slither.detectors.abstract_detector import (AbstractDetector,
                                                 DetectorClassification)


class DeprecatedSafeApprove(AbstractDetector):
    """
    Deprecated safeApprove usage detector
    """

    ARGUMENT = "erc20-deprecated-safe-approve"
    HELP = "Detects deprecated safeApprove usage"
    IMPACT = DetectorClassification.MEDIUM
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = (
        "https://github.com/crytic/slither/wiki/Detector-Documentation#erc20-deprecated-safe-approve"
    )

    WIKI_TITLE = "Deprecated safeApprove usage"
    WIKI_DESCRIPTION = "The purpose of `safeApprove` is to check that a user is either setting their allowance to zero, or setting it from zero. This is so that the user doesn't try to re-set their allowance from one non-zero number to another non-zero number where they can get front-run by the approved address using their allowance in-between those two transactions. However, this function doesn't actually solve the problem as the approval will still pass if the sandwich attack uses the rest of the remaining allowance. Such behavior lends itself to bugs, unnecessary gas usage, and a false sense of security. Because of that, `safeApprove` has been deprecated."

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """
```solidity
contract Contract {
    function _deposit() internal (uint256) {
        token.safeApprove(address(vault), 0);
    }
}
```
`safeApprove` has been deprecated."""
    # endregion wiki_exploit_scenario

    WIKI_RECOMMENDATION = "Use `safeIncreaseAllowance` and `safeDecreaseAllowance` to change an allowance."

    def detect_safe_approve(self, contract):
        ret = []
        for f in contract.functions_declared:
            calls = [
                f_called[1].solidity_signature
                for f_called in f.high_level_calls
                if isinstance(f_called[1], Function)
            ]
            if ("safeApprove(address,address,uint256)" in calls):
                ret.append(f)
        return ret

    def _detect(self):
        """Detects safeApprove usage"""
        results = []
        for c in self.contracts:
            functions = self.detect_safe_approve(c)
            for func in functions:

                info = [
                    func,
                    " calls `safeApprove`, which has been deprecated\n",
                ]

                res = self.generate_result(info)

                results.append(res)

        return results
