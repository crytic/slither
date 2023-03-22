"""
Module detecting dead code
"""
from typing import List, Tuple

from slither.core.declarations import Function, FunctionContract, Contract
from slither.detectors.abstract_detector import (
    AbstractDetector,
    DetectorClassification,
    DETECTOR_INFO,
)
from slither.utils.output import Output


class DeadCode(AbstractDetector):
    """
    Unprotected function detector
    """

    ARGUMENT = "dead-code"
    HELP = "Functions that are not used"
    IMPACT = DetectorClassification.INFORMATIONAL
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#dead-code"

    WIKI_TITLE = "Dead-code"
    WIKI_DESCRIPTION = "Functions that are not sued."

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """
```solidity
contract Contract{
    function dead_code() internal() {}
}
```
`dead_code` is not used in the contract, and make the code's review more difficult."""
    # endregion wiki_exploit_scenario

    WIKI_RECOMMENDATION = "Remove unused functions."

    def _detect(self) -> List[Output]:

        results = []

        functions_used = set()
        for contract in self.compilation_unit.contracts_derived:
            all_functionss_called = [
                f.all_internal_calls() for f in contract.functions_entry_points
            ]
            all_functions_called = [item for sublist in all_functionss_called for item in sublist]
            functions_used |= {
                f.canonical_name for f in all_functions_called if isinstance(f, Function)
            }
            all_libss_called = [f.all_library_calls() for f in contract.functions_entry_points]
            all_libs_called: List[Tuple[Contract, Function]] = [
                item for sublist in all_libss_called for item in sublist
            ]
            functions_used |= {
                lib[1].canonical_name for lib in all_libs_called if isinstance(lib, tuple)
            }
        for function in sorted(self.compilation_unit.functions, key=lambda x: x.canonical_name):
            if (
                function.visibility in ["public", "external"]
                or function.is_constructor
                or function.is_fallback
                or function.is_constructor_variables
            ):
                continue
            if function.canonical_name in functions_used:
                continue
            if isinstance(function, FunctionContract) and (
                function.contract_declarer.is_from_dependency()
            ):
                continue
            # Continue if the functon is not implemented because it means the contract is abstract
            if not function.is_implemented:
                continue
            info: DETECTOR_INFO = [function, " is never used and should be removed\n"]
            res = self.generate_result(info)
            results.append(res)

        return results
