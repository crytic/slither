"""
Module detecting local variable shadowing
"""

from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification


class LocalShadowing(AbstractDetector):
    """
    Local variable shadowing
    """

    ARGUMENT = 'shadowing-local'
    HELP = 'Local variables shadowing'
    IMPACT = DetectorClassification.LOW
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = 'https://github.com/crytic/slither/wiki/Detector-Documentation#local-variable-shadowing'

    WIKI_TITLE = 'Local Variable Shadowing'
    WIKI_DESCRIPTION = 'Detection of shadowing using local variables.'
    WIKI_EXPLOIT_SCENARIO = '''
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
`sensitive_function.owner` shadows `Bug.owner`. As a result, the use of `owner` inside `sensitive_function` might be incorrect.'''

    WIKI_RECOMMENDATION = 'Rename the local variable so as not to mistakenly overshadow any state variable/function/modifier/event definitions.'


    OVERSHADOWED_FUNCTION = "function"
    OVERSHADOWED_MODIFIER = "modifier"
    OVERSHADOWED_STATE_VARIABLE = "state variable"
    OVERSHADOWED_EVENT = "event"

    def detect_shadowing_definitions(self, contract):
        """ Detects if functions, access modifiers, events, state variables, and local variables are named after
        reserved keywords. Any such definitions are returned in a list.

        Returns:
            list of tuple: (type, contract name, definition)"""
        result = []

        # Loop through all functions + modifiers in this contract.
        for function in contract.functions + contract.modifiers:
            # We should only look for functions declared directly in this contract (not in a base contract).
            if function.contract != contract:
                continue

            # This function was declared in this contract, we check what its local variables might shadow.
            for variable in function.variables:
                overshadowed = []
                for scope_contract in [contract] + contract.inheritance:
                    # Check functions
                    for scope_function in scope_contract.functions:
                        if variable.name == scope_function.name and scope_function.contract == scope_contract:
                            overshadowed.append((self.OVERSHADOWED_FUNCTION, scope_contract.name, scope_function))
                    # Check modifiers
                    for scope_modifier in scope_contract.modifiers:
                        if variable.name == scope_modifier.name and scope_modifier.contract == scope_contract:
                            overshadowed.append((self.OVERSHADOWED_MODIFIER, scope_contract.name, scope_modifier))
                    # Check events
                    for scope_event in scope_contract.events:
                        if variable.name == scope_event.name and scope_event.contract == scope_contract:
                            overshadowed.append((self.OVERSHADOWED_EVENT, scope_contract.name, scope_event))
                    # Check state variables
                    for scope_state_variable in scope_contract.variables:
                        if variable.name == scope_state_variable.name and scope_state_variable.contract == scope_contract:
                            overshadowed.append((self.OVERSHADOWED_STATE_VARIABLE, scope_contract.name, scope_state_variable))

                # If we have found any overshadowed objects, we'll want to add it to our result list.
                if overshadowed:
                    result.append((contract.name, function.name, variable, overshadowed))

        return result

    def _detect(self):
        """ Detect shadowing local variables

        Recursively visit the calls
        Returns:
            list: {'vuln', 'filename,'contract','func', 'shadow'}

        """

        results = []
        for contract in self.contracts:
            shadows = self.detect_shadowing_definitions(contract)
            if shadows:
                for shadow in shadows:
                    local_parent_name = shadow[1]
                    local_variable = shadow[2]
                    overshadowed = shadow[3]
                    info = '{}.{}.{} (local variable @ {}) shadows:\n'.format(contract.name,
                                                                              local_parent_name,
                                                                              local_variable.name,
                                                                              local_variable.source_mapping_str)
                    for overshadowed_entry in overshadowed:
                        info += "\t- {}.{} ({} @ {})\n".format(overshadowed_entry[1],
                                                               overshadowed_entry[2],
                                                               overshadowed_entry[0],
                                                               overshadowed_entry[2].source_mapping_str)


                    # Generate relevant JSON data for this shadowing definition.
                    json = self.generate_json_result(info)
                    self.add_variable_to_json(local_variable, json)
                    for overshadowed_entry in overshadowed:
                        if overshadowed_entry[0] in [self.OVERSHADOWED_FUNCTION, self.OVERSHADOWED_MODIFIER,
                                                     self.OVERSHADOWED_EVENT]:
                            self.add_function_to_json(overshadowed_entry[2], json)
                        elif overshadowed_entry[0] == self.OVERSHADOWED_STATE_VARIABLE:
                            self.add_variable_to_json(overshadowed_entry[2], json)
                    results.append(json)

        return results
