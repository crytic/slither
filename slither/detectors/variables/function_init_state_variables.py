"""
Module detecting state variables initializing from an immediate function call (prior to constructor run).
"""
from typing import List

from slither.core.declarations.contract import Contract
from slither.core.declarations.function import Function
from slither.core.variables.state_variable import StateVariable
from slither.detectors.abstract_detector import (
    AbstractDetector,
    DetectorClassification,
    DETECTOR_INFO,
)
from slither.utils.output import Output
from slither.visitors.expression.export_values import ExportValues


def detect_function_init_state_vars(contract: Contract) -> List[StateVariable]:
    """
    Detect any state variables that are initialized from an immediate function call (prior to constructor run).
    :param contract: The contract to detect state variable definitions for.
    :return: A list of all state variables defined in the given contract that meet the specified criteria.
    """
    results = []

    # Loop for each state variable explicitly defined in this contract.
    for state_variable in contract.variables:

        # Skip this variable if it is inherited and not explicitly defined in this contract definition.
        if state_variable.contract != contract:
            continue

        # If it has an expression, we try to break it down to identify if it contains a function call, or reference
        # to a non-constant state variable.
        if state_variable.expression:
            exported_values = ExportValues(state_variable.expression).result()
            for exported_value in exported_values:
                if (
                    isinstance(exported_value, StateVariable) and not exported_value.is_constant
                ) or (isinstance(exported_value, Function) and not exported_value.pure):
                    results.append(state_variable)
                    break

    return results


class FunctionInitializedState(AbstractDetector):
    """
    State variables initializing from an immediate function call (prior to constructor run).
    """

    ARGUMENT = "function-init-state"
    HELP = "Function initializing state variables"
    IMPACT = DetectorClassification.INFORMATIONAL
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = (
        "https://github.com/crytic/slither/wiki/Detector-Documentation#function-initializing-state"
    )

    WIKI_TITLE = "Function Initializing State"
    WIKI_DESCRIPTION = "Detects the immediate initialization of state variables through function calls that are not pure/constant, or that use non-constant state variable."

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """
```solidity
contract StateVarInitFromFunction {

    uint public v = set(); // Initialize from function (sets to 77)
    uint public w = 5;
    uint public x = set(); // Initialize from function (sets to 88)
    address public shouldntBeReported = address(8);

    constructor(){
        // The constructor is run after all state variables are initialized.
    }

    function set() public  returns(uint)  {
        // If this function is being used to initialize a state variable declared
        // before w, w will be zero. If it is declared after w, w will be set.
        if(w == 0) {
            return 77;
        }

        return 88;
    }
}
```
In this case, users might intend a function to return a value a state variable can initialize with, without realizing the context for the contract is not fully initialized. 
In the example above, the same function sets two different values for state variables because it checks a state variable that is not yet initialized in one case, and is initialized in the other. 
Special care must be taken when initializing state variables from an immediate function call so as not to incorrectly assume the state is initialized.
"""
    # endregion wiki_exploit_scenario

    WIKI_RECOMMENDATION = "Remove any initialization of state variables via non-constant state variables or function calls. If variables must be set upon contract deployment, locate initialization in the constructor instead."

    def _detect(self) -> List[Output]:
        """
        Detect state variables defined from an immediate function call (pre-contract deployment).

        Recursively visit the calls
        Returns:
            list: {'vuln', 'filename,'contract','func', 'shadow'}

        """
        results = []
        for contract in self.contracts:
            state_variables = detect_function_init_state_vars(contract)
            if state_variables:
                for state_variable in state_variables:
                    info: DETECTOR_INFO = [
                        state_variable,
                        " is set pre-construction with a non-constant function or state variable:\n",
                    ]
                    info += [f"\t- {state_variable.expression}\n"]
                    json = self.generate_result(info)
                    results.append(json)

        return results
