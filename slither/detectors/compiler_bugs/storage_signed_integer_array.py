"""
Module detecting storage signed integer array bug
"""

from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.core.cfg.node import NodeType
from slither.core.solidity_types import ArrayType
from slither.core.solidity_types.elementary_type import Int, ElementaryType
from slither.core.variables.local_variable import LocalVariable
from slither.core.variables.state_variable import StateVariable
from slither.slithir.operations.assignment import Assignment
from slither.slithir.operations.init_array import InitArray

vulnerable_solc_versions = [
    "0.4.7",
    "0.4.8",
    "0.4.9",
    "0.4.10",
    "0.4.11",
    "0.4.12",
    "0.4.13",
    "0.4.14",
    "0.4.15",
    "0.4.16",
    "0.4.17",
    "0.4.18",
    "0.4.19",
    "0.4.20",
    "0.4.21",
    "0.4.22",
    "0.4.23",
    "0.4.24",
    "0.4.25",
    "0.5.0",
    "0.5.1",
    "0.5.2",
    "0.5.3",
    "0.5.4",
    "0.5.5",
    "0.5.6",
    "0.5.7",
    "0.5.8",
    "0.5.9",
    "0.5.10",
]


class StorageSignedIntegerArray(AbstractDetector):
    """
    Storage signed integer array
    """

    ARGUMENT = "storage-array"
    HELP = "Signed storage integer array compiler bug"
    IMPACT = DetectorClassification.HIGH
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = (
        "https://github.com/crytic/slither/wiki/Detector-Documentation#storage-signed-integer-array"
    )
    WIKI_TITLE = "Storage Signed Integer Array"
    WIKI_DESCRIPTION = """`solc` versions `0.4.7`-`0.5.10` contain [a compiler bug](https://blog.ethereum.org/2019/06/25/solidity-storage-array-bugs)
leading to incorrect values in signed integer arrays."""
    WIKI_EXPLOIT_SCENARIO = """
```solidity
contract A {
	int[3] ether_balances; // storage signed integer array
	function bad0() private {
		// ...
		ether_balances = [-1, -1, -1];
		// ...
	}
}
```
`bad0()` uses a (storage-allocated) signed integer array state variable to store the ether balances of three accounts.  
`-1` is supposed to indicate uninitialized values but the Solidity bug makes these as `1`, which could be exploited by the accounts.
"""
    WIKI_RECOMMENDATION = "Use a compiler version >= `0.5.10`."

    @staticmethod
    def _is_vulnerable_type(ir):
        """
        Detect if the IR lvalue is a vulnerable type
        Must be a storage allocation, and an array of Int
        Assume the IR is a InitArray, or an Assignement to an ArrayType
        """
        # Storage allocation
        # Base type is signed integer
        return (
            (
                isinstance(ir.lvalue, StateVariable)
                or (isinstance(ir.lvalue, LocalVariable) and ir.lvalue.is_storage)
            )
            and isinstance(ir.lvalue.type.type, ElementaryType)
            and ir.lvalue.type.type.type in Int
        )

    def detect_storage_signed_integer_arrays(self, contract):
        """
        Detects and returns all nodes with storage-allocated signed integer array init/assignment
        :param contract: Contract to detect within
        :return: A list of tuples with (function, node) where function node has storage-allocated signed integer array init/assignment
        """
        # Create our result set.
        results = set()

        # Loop for each function and modifier.
        for function in contract.functions_and_modifiers_declared:
            # Loop for every node in this function, looking for storage-allocated
            # signed integer array initializations/assignments
            for node in function.nodes:
                if node.type == NodeType.EXPRESSION:
                    for ir in node.irs:
                        # Storage-allocated signed integer array initialization expression
                        if isinstance(ir, InitArray) and self._is_vulnerable_type(ir):
                            results.add((function, node))
                        # Assignment expression with lvalue being a storage-allocated signed integer array and
                        # rvalue being a signed integer array of different base type than lvalue
                        if (
                            isinstance(ir, Assignment)
                            and isinstance(ir.lvalue.type, ArrayType)
                            and self._is_vulnerable_type(ir)
                            # Base type is signed integer and lvalue base type is different from rvalue base type
                            and ir.lvalue.type.type != ir.rvalue.type.type
                        ):
                            results.add((function, node))

        # Return the resulting set of tuples
        return results

    def _detect(self):
        """
        Detect storage signed integer array init/assignment
        """
        results = []
        if self.slither.solc_version not in vulnerable_solc_versions:
            return results
        for contract in self.contracts:
            storage_signed_integer_arrays = self.detect_storage_signed_integer_arrays(contract)
            for function, node in storage_signed_integer_arrays:
                contract_info = ["Contract ", contract, " \n"]
                function_info = ["\t- Function ", function, "\n"]
                node_info = ["\t\t- ", node, " has a storage signed integer array assignment\n"]
                res = self.generate_result(contract_info + function_info + node_info)
                results.append(res)

        return results
