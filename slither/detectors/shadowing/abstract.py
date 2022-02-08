"""
Module detecting shadowing variables on abstract contract
Recursively check the called functions
"""
from typing import List

from slither.core.declarations import Contract
from slither.core.variables.state_variable import StateVariable
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.utils.output import Output, AllSupportedOutput


def detect_shadowing(contract: Contract) -> List[List[StateVariable]]:
    ret: List[List[StateVariable]] = []
    variables_fathers = []
    for father in contract.inheritance:
        if all(not f.is_implemented for f in father.functions + list(father.modifiers)):
            variables_fathers += father.state_variables_declared

    var: StateVariable
    for var in contract.state_variables_declared:
        shadow: List[StateVariable] = [v for v in variables_fathers if v.name == var.name]
        if shadow:
            ret.append([var] + shadow)
    return ret


class ShadowingAbstractDetection(AbstractDetector):
    """
    Shadowing detection
    """

    ARGUMENT = "shadowing-abstract"
    HELP = "State variables shadowing from abstract contracts"
    IMPACT = DetectorClassification.MEDIUM
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#state-variable-shadowing-from-abstract-contracts"

    WIKI_TITLE = "State variable shadowing from abstract contracts"
    WIKI_DESCRIPTION = "Detection of state variables shadowed from abstract contracts."

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """
```solidity
contract BaseContract{
    address owner;
}

contract DerivedContract is BaseContract{
    address owner;
}
```
`owner` of `BaseContract` is shadowed in `DerivedContract`."""
    # endregion wiki_exploit_scenario

    WIKI_RECOMMENDATION = "Remove the state variable shadowing."

    def _detect(self) -> List[Output]:
        """Detect shadowing

        Recursively visit the calls
        Returns:
            list: {'vuln', 'filename,'contract','func', 'shadow'}

        """
        results: List[Output] = []
        for contract in self.contracts:
            shadowing = detect_shadowing(contract)
            if shadowing:
                for all_variables in shadowing:
                    shadow = all_variables[0]
                    variables = all_variables[1:]
                    info: List[AllSupportedOutput] = [shadow, " shadows:\n"]
                    for var in variables:
                        info += ["\t- ", var, "\n"]

                    res = self.generate_result(info)

                    results.append(res)

        return results
