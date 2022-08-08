"""
Module detecting suicidal contract

A suicidal contract is an unprotected function that calls selfdestruct
"""
from typing import List

from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.core.declarations import Function, Contract
from slither.utils.output import Output


class ProtectedVariables(AbstractDetector):

    ARGUMENT = "protected-vars"
    HELP = "Detected unprotected variables"
    IMPACT = DetectorClassification.HIGH
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#protected-variables"

    WIKI_TITLE = "Protected Variables"
    WIKI_DESCRIPTION = "Detect unprotected variable that are marked protected"

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """
```solidity
contract Buggy{

    /// @custom:security write-protection="onlyOwner()"
    address owner;

    function set_protected() public onlyOwner(){
        owner = msg.sender;
    }

    function set_not_protected() public{
        owner = msg.sender;
    }
}    
```
`owner` must be always written by function using `onlyOwner` (`write-protection="onlyOwner()"`), however anyone can call `set_not_protected`.
"""
    # endregion wiki_exploit_scenario

    WIKI_RECOMMENDATION = "Add access controls to the vulnerable function"

    def _analyze_function(self, function: Function, contract: Contract) -> List[Output]:
        results = []

        for state_variable_written in function.state_variables_written:
            if state_variable_written.write_protection:
                for function_sig in state_variable_written.write_protection:
                    function_protection = contract.get_function_from_signature(function_sig)
                    if not function_protection:
                        function_protection = contract.get_modifier_from_signature(function_sig)
                    if not function_protection:
                        self.logger.error(f"{function_sig} not found")
                        continue
                    if function_protection not in function.all_internal_calls():
                        info = [
                            function,
                            " should have ",
                            function_protection,
                            " to protect ",
                            state_variable_written,
                            "\n",
                        ]

                        res = self.generate_result(info)
                        results.append(res)
        return results

    def _detect(self):
        """Detect the suicidal functions"""
        results = []
        for contract in self.compilation_unit.contracts_derived:
            for function in contract.functions_entry_points:
                results += self._analyze_function(function, contract)

        return results
