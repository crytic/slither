"""
Module detecting assignment of array length
"""

from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.core.cfg.node import NodeType
from slither.slithir.operations import Assignment, Length
from slither.slithir.variables.reference import ReferenceVariable
from slither.slithir.operations.binary import Binary
from slither.analyses.data_dependency.data_dependency import is_tainted


def detect_array_length_assignment(contract):
    """
    Detects and returns all nodes which assign array length.
    :param contract: Contract to detect assignment within.
    :return: A list of tuples with (Variable, node) where Variable references an array whose length was set by node.
    """

    # Create our result set.
    results = set()

    # Loop for each function and modifier.
    # pylint: disable=too-many-nested-blocks
    for function in contract.functions_and_modifiers_declared:
        # Define a set of reference variables which refer to array length.
        array_length_refs = set()

        # Loop for every node in this function, looking for expressions where array length references are made,
        # and subsequent expressions where array length references are assigned to.
        for node in function.nodes:
            if node.type == NodeType.EXPRESSION:
                for ir in node.irs:

                    # First we look for the member access for 'length', for which a reference is created.
                    # We add the reference to our list of array length references.
                    if isinstance(ir, Length):  # a
                        #                            if ir.variable_right == "length":
                        array_length_refs.add(ir.lvalue)

                    # If we have an assignment/binary operation, verify the left side refers to a reference variable
                    # which is in our list or array length references. (Array length is being assigned to).
                    elif isinstance(ir, (Assignment, Binary)):
                        if isinstance(ir.lvalue, ReferenceVariable):
                            if ir.lvalue in array_length_refs and any(
                                is_tainted(v, contract) for v in ir.read
                            ):
                                # the taint is not precise enough yet
                                # as a result, REF_0 = REF_0 + 1
                                # where REF_0 points to a LENGTH operation
                                # is considered as tainted
                                if ir.lvalue in ir.read:
                                    continue
                                results.add(node)
                                break

    # Return the resulting set of nodes which set array length.
    return results


class ArrayLengthAssignment(AbstractDetector):
    """
    Array length assignment
    """

    ARGUMENT = "controlled-array-length"
    HELP = "Tainted array length assignment"
    IMPACT = DetectorClassification.HIGH
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#array-length-assignment"

    WIKI_TITLE = "Array Length Assignment"
    WIKI_DESCRIPTION = """Detects the direct assignment of an array's length."""

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """
```solidity
contract A {
	uint[] testArray; // dynamic size array

	function f(uint usersCount) public {
		// ...
		testArray.length = usersCount;
		// ...
	}

	function g(uint userIndex, uint val) public {
		// ...
		testArray[userIndex] = val;
		// ...
	}
}
```
Contract storage/state-variables are indexed by a 256-bit integer.
The user can set the array length to `2**256-1` in order to index all storage slots. 
In the example above, one could call the function `f` to set the array length, then call the function `g` to control any storage slot desired. 
Note that storage slots here are indexed via a hash of the indexers; nonetheless, all storage will still be accessible and could be controlled by the attacker."""
    # endregion wiki_exploit_scenario

    # region wiki_recommendation
    WIKI_RECOMMENDATION = """Do not allow array lengths to be set directly set; instead, opt to add values as needed.
Otherwise, thoroughly review the contract to ensure a user-controlled variable cannot reach an array length assignment."""
    # endregion wiki_recommendation

    def _detect(self):
        """
        Detect array length assignments
        """
        results = []
        # Starting from 0.6 .length is read only
        if self.compilation_unit.solc_version >= "0.6.":
            return results
        for contract in self.contracts:
            array_length_assignments = detect_array_length_assignment(contract)
            if array_length_assignments:
                contract_info = [
                    contract,
                    " contract sets array length with a user-controlled value:\n",
                ]
                for node in array_length_assignments:
                    node_info = contract_info + ["\t- ", node, "\n"]
                    res = self.generate_result(node_info)
                    results.append(res)

        return results
