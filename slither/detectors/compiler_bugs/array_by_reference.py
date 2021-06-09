"""
Detects the passing of arrays located in memory to functions which expect to modify arrays via storage reference.
"""

from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.core.solidity_types.array_type import ArrayType
from slither.core.variables.state_variable import StateVariable
from slither.core.variables.local_variable import LocalVariable
from slither.slithir.operations.high_level_call import HighLevelCall
from slither.slithir.operations.internal_call import InternalCall


class ArrayByReference(AbstractDetector):
    """
    Detects passing of arrays located in memory to functions which expect to modify arrays via storage reference.
    """

    ARGUMENT = "array-by-reference"
    HELP = "Modifying storage array by value"
    IMPACT = DetectorClassification.HIGH
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#modifying-storage-array-by-value"

    WIKI_TITLE = "Modifying storage array by value"
    WIKI_DESCRIPTION = (
        "Detect arrays passed to a function that expects reference to a storage array"
    )

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """
```solidity
contract Memory {
    uint[1] public x; // storage

    function f() public {
        f1(x); // update x
        f2(x); // do not update x
    }

    function f1(uint[1] storage arr) internal { // by reference
        arr[0] = 1;
    }

    function f2(uint[1] arr) internal { // by value
        arr[0] = 2;
    }
}
```

Bob calls `f()`. Bob assumes that at the end of the call `x[0]` is 2, but it is 1.
As a result, Bob's usage of the contract is incorrect."""
    # endregion wiki_exploit_scenario

    WIKI_RECOMMENDATION = "Ensure the correct usage of `memory` and `storage` in the function parameters. Make all the locations explicit."

    @staticmethod
    def get_funcs_modifying_array_params(contracts):
        """
        Obtains a set of functions which take arrays not located in storage as parameters, and writes to them.
        :param contracts: The collection of contracts to check functions in.
        :return: A set of functions which take an array not located in storage as a parameter and writes to it.
        """
        # Initialize our resulting set of functions which modify non-reference array parameters
        results = set()

        # Loop through all functions in all contracts.
        for contract in contracts:
            for function in contract.functions_declared:

                # Skip any constructor functions.
                if function.is_constructor:
                    continue

                # Determine if this function takes an array as a parameter and the location isn't storage.
                # If it has been written to, we know this sets an non-storage-ref array.
                for param in function.parameters:
                    if isinstance(param.type, ArrayType) and param.location != "storage":
                        if param in function.variables_written:
                            results.add(function)
                            break

        return results

    @staticmethod
    def detect_calls_passing_ref_to_function(contracts, array_modifying_funcs):
        """
        Obtains all calls passing storage arrays by value to a function which cannot write to them successfully.
        :param contracts: The collection of contracts to check for problematic calls in.
        :param array_modifying_funcs: The collection of functions which take non-storage arrays as input and writes to
        them.
        :return: A list of tuples (calling_node, affected_argument, invoked_function) which denote all problematic
        nodes invoking a function with some storage array argument where the invoked function seemingly attempts to
        write to the array unsuccessfully.
        """
        # Define our resulting array.
        results = []

        # Verify we have functions in our list to check for.
        if not array_modifying_funcs:
            return results

        # Loop for each node in each function/modifier in each contract
        # pylint: disable=too-many-nested-blocks
        for contract in contracts:
            for function in contract.functions_and_modifiers_declared:
                for node in function.nodes:

                    # If this node has no expression, skip it.
                    if not node.expression:
                        continue

                    for ir in node.irs:
                        # Verify this is a high level call.
                        if not isinstance(ir, (HighLevelCall, InternalCall)):
                            continue

                        # Verify this references a function in our array modifying functions collection.
                        if ir.function not in array_modifying_funcs:
                            continue

                        # Verify one of these parameters is an array in storage.
                        for arg in ir.arguments:
                            # Verify this argument is a variable that is an array type.
                            if not isinstance(arg, (StateVariable, LocalVariable)):
                                continue
                            if not isinstance(arg.type, ArrayType):
                                continue

                            # If it is a state variable OR a local variable referencing storage, we add it to the list.
                            if isinstance(arg, StateVariable) or (
                                isinstance(arg, LocalVariable) and arg.location == "storage"
                            ):
                                results.append((node, arg, ir.function))
        return results

    def _detect(self):
        """
        Detects passing of arrays located in memory to functions which expect to modify arrays via storage reference.
        :return: The JSON results of the detector, which contains the calling_node, affected_argument_variable and
        invoked_function for each result found.
        """
        results = []
        array_modifying_funcs = self.get_funcs_modifying_array_params(self.contracts)
        problematic_calls = self.detect_calls_passing_ref_to_function(
            self.contracts, array_modifying_funcs
        )

        if problematic_calls:
            for calling_node, affected_argument, invoked_function in problematic_calls:
                info = [
                    calling_node.function,
                    " passes array ",
                    affected_argument,
                    "by reference to ",
                    invoked_function,
                    "which only takes arrays by value\n",
                ]

                res = self.generate_result(info)
                results.append(res)

        return results
