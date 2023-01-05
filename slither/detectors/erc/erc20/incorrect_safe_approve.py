"""
Module detecting incorrect safeApprove usage
"""

from slither.core.declarations.function import Function
from slither.core.variables.variable import Variable
from slither.detectors.abstract_detector import (AbstractDetector,
                                                 DetectorClassification)
from slither.slithir.variables.constant import Constant


class IncorrectSafeApprove(AbstractDetector):
    """
    Incorrect safeApprove usage detector
    """

    ARGUMENT = "incorrect-safe-approve"
    HELP = "Detects incorrect safeApprove usage"
    IMPACT = DetectorClassification.MEDIUM
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = (
        "https://github.com/crytic/slither/wiki/Detector-Documentation#incorrect-safe-approve"
    )

    WIKI_TITLE = "Incorrect safeApprove usage"
    WIKI_DESCRIPTION = "The `safeApprove` function of the OpenZeppelin `SafeERC20` library prevents changing an allowance between non-zero values to mitigate a possible front-running attack. Instead, the `safeIncreaseAllowance` and `safeDecreaseAllowance` functions should be used. `safeApprove` should only be called when setting an initial allowance, or when resetting it to zero."

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """
```solidity
contract Contract {
    function _deposit() internal (uint256) {
        if(token.allowance(address(this), address(vault)) < token.balanceOf(address(this))) {
            token.safeApprove(address(vault), type(uint256).max);
        }
        return vault.deposit();
    }
}
```
If the existing allowance is non-zero, then `safeApprove` will revert, causing deposits to fail leading to denial-of-service."""
    # endregion wiki_exploit_scenario

    WIKI_RECOMMENDATION = "Use `safeIncreaseAllowance` and `safeDecreaseAllowance` to change an allowance between non-zero values."

    @staticmethod
    def is_zero_argument(f):
        for node in f.nodes:
            for ir in node.irs:
                for read in ir.read:
                    if isinstance(read, Constant):
                        return read == 0
                    elif isinstance(read, Variable) and read.expression is not None:
                        return str(read.expression) == "0"

    def detect_safe_approve_non_zero(self, contract):
        ret = []
        for f in contract.functions_declared:
            calls = [
                f_called[1].solidity_signature
                for f_called in f.high_level_calls
                if isinstance(f_called[1], Function)
            ]
            if (
                "safeApprove(address,address,uint256)" in calls and
                not self.is_zero_argument(f)
            ):
                ret.append(f)
        return ret

    def _detect(self):
        """Detects incorrect safeApprove usage"""
        results = []
        for c in self.contracts:
            functions = self.detect_safe_approve_non_zero(c)
            for func in functions:

                info = [
                    func,
                    " calls `safeApprove` with a non-zero value\n",
                ]

                res = self.generate_result(info)

                results.append(res)

        return results
