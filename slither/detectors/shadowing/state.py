"""
Module detecting shadowing of state variables
"""

from typing import List

from slither.core.declarations import Contract
from slither.core.variables.state_variable import StateVariable
from slither.detectors.abstract_detector import (
    AbstractDetector,
    DetectorClassification,
    DETECTOR_INFO,
)
from slither.detectors.shadowing.common import is_upgradable_gap_variable
from slither.utils.output import Output


def detect_shadowing(contract: Contract) -> List[List[StateVariable]]:
    ret = []
    variables_fathers = []
    for father in contract.inheritance:
        if any(f.is_implemented for f in father.functions + father.modifiers):
            variables_fathers += father.state_variables_declared

    for var in contract.state_variables_declared:
        # Ignore __gap variables for updatable contracts
        if is_upgradable_gap_variable(contract, var):
            continue

        shadow = [v for v in variables_fathers if v.name == var.name]
        if shadow:
            ret.append([var] + shadow)
    return ret


class StateShadowing(AbstractDetector):
    """
    Shadowing of state variable
    """

    ARGUMENT = "shadowing-state"
    HELP = "State variables shadowing"
    IMPACT = DetectorClassification.HIGH
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#state-variable-shadowing"

    WIKI_TITLE = "State variable shadowing"
    WIKI_DESCRIPTION = "Detection of state variables shadowed."

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """
```solidity
contract BaseContract{
    address owner;

    modifier isOwner(){
        require(owner == msg.sender);
        _;
    }

}

contract DerivedContract is BaseContract{
    address owner;

    constructor(){
        owner = msg.sender;
    }

    function withdraw() isOwner() external{
        msg.sender.transfer(this.balance);
    }
}
```
`owner` of `BaseContract` is never assigned and the modifier `isOwner` does not work."""
    # endregion wiki_exploit_scenario

    WIKI_RECOMMENDATION = "Remove the state variable shadowing."

    def _detect(self) -> List[Output]:
        """Detect shadowing

        Recursively visit the calls
        Returns:
            list: {'vuln', 'filename,'contract','func', 'shadow'}

        """
        results = []
        for c in self.contracts:
            shadowing = detect_shadowing(c)
            if shadowing:
                for all_variables in shadowing:
                    shadow = all_variables[0]
                    variables = all_variables[1:]
                    info: DETECTOR_INFO = [shadow, " shadows:\n"]
                    for var in variables:
                        info += ["\t- ", var, "\n"]

                    res = self.generate_result(info)
                    results.append(res)

        return results
