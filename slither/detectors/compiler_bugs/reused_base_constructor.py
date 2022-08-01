"""
Module detecting re-used base constructors in inheritance hierarchy.
"""

from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification


# Helper: adds explicitly called constructors with arguments to the results lookup.
def _add_constructors_with_args(
    base_constructors, called_by_constructor, current_contract, results
):
    for explicit_base_constructor in base_constructors:
        if len(explicit_base_constructor.parameters) > 0:
            if explicit_base_constructor not in results:
                results[explicit_base_constructor] = []
            results[explicit_base_constructor] += [(current_contract, called_by_constructor)]


class ReusedBaseConstructor(AbstractDetector):
    """
    Re-used base constructors
    """

    ARGUMENT = "reused-constructor"
    HELP = "Reused base constructor"
    IMPACT = DetectorClassification.MEDIUM
    # The confidence is medium, because prior Solidity 0.4.22, we cant differentiate
    # contract C is A() {
    # to
    # contract C is A {
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#reused-base-constructors"

    WIKI_TITLE = "Reused base constructors"
    WIKI_DESCRIPTION = "Detects if the same base constructor is called with arguments from two different locations in the same inheritance hierarchy."

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """
```solidity
pragma solidity ^0.4.0;

contract A{
    uint num = 5;
    constructor(uint x) public{
        num += x;
    }
}

contract B is A{
    constructor() A(2) public { /* ... */ }
}

contract C is A {
    constructor() A(3) public { /* ... */ }
}

contract D is B, C {
    constructor() public { /* ... */ }
}

contract E is B {
    constructor() A(1) public { /* ... */ }
}
```
The constructor of `A` is called multiple times in `D` and `E`:
- `D` inherits from `B` and `C`, both of which construct `A`.
- `E` only inherits from `B`, but `B` and `E` construct `A`.
."""
    # endregion wiki_exploit_scenario

    WIKI_RECOMMENDATION = "Remove the duplicate constructor call."

    def _detect_explicitly_called_base_constructors(self, contract):
        """
        Detects explicitly calls to base constructors with arguments in the inheritance hierarchy.
        :param contract: The contract to detect explicit calls to a base constructor with arguments to.
        :return: Dictionary of function:list(tuple): { constructor : [(invoking_contract, called_by_constructor]}
        """
        results = {}

        # Create a set to track all completed contracts
        processed_contracts = set()
        queued_contracts = [contract] + contract.inheritance

        # Loop until there are no queued contracts left.
        while len(queued_contracts) > 0:

            # Pop a contract off the front of the queue, if it has already been processed, we stop.
            current_contract = queued_contracts.pop(0)
            if current_contract in processed_contracts:
                continue

            # Add this contract to the processed contracts
            processed_contracts.add(current_contract)

            # Prior Solidity 0.4.22, the constructor would appear two times
            # Leading to several FPs
            # As the result, we might miss some TPs if the reused is due to the constructor called
            # In the contract definition
            if self.compilation_unit.solc_version >= "0.4.22":
                # Find all base constructors explicitly called from the contract definition with arguments.
                _add_constructors_with_args(
                    current_contract.explicit_base_constructor_calls,
                    False,
                    current_contract,
                    results,
                )

            # Find all base constructors explicitly called from the constructor definition with arguments.
            if current_contract.constructors_declared:
                _add_constructors_with_args(
                    current_contract.constructors_declared.explicit_base_constructor_calls,
                    True,
                    current_contract,
                    results,
                )

        return results

    def _detect(self):
        """
        Detect reused base constructors.
        :return: Returns a list of JSON results.
        """

        results = []

        # The bug is not possible with solc >= 0.5.0
        if not self.compilation_unit.solc_version.startswith("0.4."):
            return []

        # Loop for each contract
        for contract in self.contracts:

            # Detect all locations which all underlying base constructors with arguments were called from.
            called_base_constructors = self._detect_explicitly_called_base_constructors(contract)
            for base_constructor, call_list in called_base_constructors.items():
                # Only report if there are multiple calls to the same base constructor.
                if len(call_list) <= 1:
                    continue

                # Generate data to output.
                info = [
                    contract,
                    " gives base constructor ",
                    base_constructor,
                    " arguments more than once in inheritance hierarchy:\n",
                ]

                for (calling_contract, called_by_constructor) in call_list:
                    info += [
                        "\t- From ",
                        calling_contract,
                        f" {'constructor' if called_by_constructor else 'contract'} definition\n",
                    ]

                res = self.generate_result(info)
                results.append(res)

        return results
