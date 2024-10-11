"""
Module detecting local variable shadowing
"""
from typing import List, Tuple, Union

from slither.core.declarations.contract import Contract
from slither.core.declarations.event import Event
from slither.core.declarations.function_contract import FunctionContract
from slither.core.declarations.modifier import Modifier
from slither.core.variables.local_variable import LocalVariable
from slither.core.variables.state_variable import StateVariable
from slither.detectors.abstract_detector import (
    AbstractDetector,
    DetectorClassification,
    DETECTOR_INFO,
)
from slither.utils.output import Output


class LocalShadowing(AbstractDetector):
    """
    Local variable shadowing
    """

    ARGUMENT = "shadowing-local"
    HELP = "Local variables shadowing"
    IMPACT = DetectorClassification.LOW
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#local-variable-shadowing"

    WIKI_TITLE = "Local variable shadowing"
    WIKI_DESCRIPTION = "Detection of shadowing using local variables."

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """
```solidity
pragma solidity ^0.4.24;

contract Bug {
    uint owner;

    function sensitive_function(address owner) public {
        // ...
        require(owner == msg.sender);
    }

    function alternate_sensitive_function() public {
        address owner = msg.sender;
        // ...
        require(owner == msg.sender);
    }
}
```
`sensitive_function.owner` shadows `Bug.owner`. As a result, the use of `owner` in `sensitive_function` might be incorrect."""
    # endregion wiki_exploit_scenario

    WIKI_RECOMMENDATION = "Rename the local variables that shadow another component."

    OVERSHADOWED_FUNCTION = "function"
    OVERSHADOWED_MODIFIER = "modifier"
    OVERSHADOWED_STATE_VARIABLE = "state variable"
    OVERSHADOWED_EVENT = "event"
    OVERSHADOWED_RETURN_VARIABLE = "return variable"

    # pylint: disable=too-many-branches
    def detect_shadowing_definitions(
        self, contract: Contract
    ) -> List[
        Union[
            Tuple[LocalVariable, List[Tuple[str, StateVariable]]],
            Tuple[LocalVariable, List[Tuple[str, FunctionContract]]],
            Tuple[LocalVariable, List[Tuple[str, Modifier]]],
            Tuple[LocalVariable, List[Tuple[str, Event]]],
        ]
    ]:
        """Detects if functions, access modifiers, events, state variables, and local variables are named after
        reserved keywords. Any such definitions are returned in a list.

        Returns:
            list of tuple: (type, contract name, definition)"""
        result: List[
            Union[
                Tuple[LocalVariable, List[Tuple[str, StateVariable]]],
                Tuple[LocalVariable, List[Tuple[str, FunctionContract]]],
                Tuple[LocalVariable, List[Tuple[str, Modifier]]],
                Tuple[LocalVariable, List[Tuple[str, Event]]],
            ]
        ] = []

        # Loop through all functions + modifiers in this contract.
        for function in contract.functions + list(contract.modifiers):
            # We should only look for functions declared directly in this contract (not in a base contract).
            if function.contract_declarer != contract:
                continue

            # This function was declared in this contract, we check what its local variables might shadow.
            for variable in function.variables:
                overshadowed = []
                for scope_contract in [contract] + contract.inheritance:
                    # Check functions
                    for scope_function in scope_contract.functions_declared:
                        if variable.name == scope_function.name:
                            overshadowed.append((self.OVERSHADOWED_FUNCTION, scope_function))
                    # Check modifiers
                    for scope_modifier in scope_contract.modifiers_declared:
                        if variable.name == scope_modifier.name:
                            overshadowed.append((self.OVERSHADOWED_MODIFIER, scope_modifier))
                    # Check events
                    for scope_event in scope_contract.events_declared:
                        if variable.name == scope_event.name:
                            overshadowed.append((self.OVERSHADOWED_EVENT, scope_event))
                    # Check state variables
                    for scope_state_variable in scope_contract.state_variables_declared:
                        if variable.name == scope_state_variable.name:
                            overshadowed.append(
                                (self.OVERSHADOWED_STATE_VARIABLE, scope_state_variable)
                            )
                    # Check named return variables
                    for named_return in function.returns:
                        # Shadowed local delcarations in the same function will have "_scope_" in their name.
                        # See `FunctionSolc._add_local_variable`
                        if (
                            "_scope_" in variable.name
                            and variable.name.split("_scope_")[0] == named_return.name
                        ):
                            overshadowed.append((self.OVERSHADOWED_RETURN_VARIABLE, named_return))

                # If we have found any overshadowed objects, we'll want to add it to our result list.
                if overshadowed:
                    result.append((variable, overshadowed))

        return result

    def _detect(self) -> List[Output]:
        """Detect shadowing local variables

        Recursively visit the calls
        Returns:
            list: {'vuln', 'filename,'contract','func', 'shadow'}

        """

        results = []
        for contract in self.contracts:
            shadows = self.detect_shadowing_definitions(contract)
            if shadows:
                for shadow in shadows:
                    local_variable = shadow[0]
                    overshadowed = shadow[1]
                    info: DETECTOR_INFO = [local_variable, " shadows:\n"]
                    for overshadowed_entry in overshadowed:
                        info += [
                            "\t- ",
                            overshadowed_entry[1],
                            f" ({overshadowed_entry[0]})\n",
                        ]

                    # Generate relevant JSON data for this shadowing definition.
                    res = self.generate_result(info)

                    results.append(res)

        return results
