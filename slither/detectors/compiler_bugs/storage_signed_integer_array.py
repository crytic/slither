"""
Module detecting storage signed integer array bug
"""
from typing import List, Tuple, Set

from slither.core.declarations import Function, Contract
from slither.detectors.abstract_detector import (
    AbstractDetector,
    DetectorClassification,
    make_solc_versions,
    DETECTOR_INFO,
)
from slither.core.cfg.node import NodeType, Node
from slither.core.solidity_types import ArrayType
from slither.core.solidity_types.elementary_type import Int, ElementaryType
from slither.core.variables.local_variable import LocalVariable
from slither.core.variables.state_variable import StateVariable
from slither.slithir.operations import Operation, OperationWithLValue
from slither.slithir.operations.assignment import Assignment
from slither.slithir.operations.init_array import InitArray
from slither.utils.output import Output


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

    # region wiki_description
    WIKI_DESCRIPTION = """`solc` versions `0.4.7`-`0.5.9` contain [a compiler bug](https://blog.ethereum.org/2019/06/25/solidity-storage-array-bugs)
leading to incorrect values in signed integer arrays."""
    # endregion wiki_description

    # region wiki_exploit_scenario
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
    # endregion wiki_exploit_scenario

    WIKI_RECOMMENDATION = "Use a compiler version >= `0.5.10`."

    VULNERABLE_SOLC_VERSIONS = make_solc_versions(4, 7, 25) + make_solc_versions(5, 0, 9)

    @staticmethod
    def _is_vulnerable_type(ir: Operation) -> bool:
        """
        Detect if the IR lvalue is a vulnerable type
        Must be a storage allocation, and an array of Int
        Assume the IR is a InitArray, or an Assignement to an ArrayType
        """
        # Storage allocation
        # Base type is signed integer
        if not isinstance(ir, OperationWithLValue):
            return False

        return (
            (
                isinstance(ir.lvalue, StateVariable)
                or (isinstance(ir.lvalue, LocalVariable) and ir.lvalue.is_storage)
            )
            and isinstance(ir.lvalue.type.type, ElementaryType)  # type: ignore
            and ir.lvalue.type.type.type in Int  # type: ignore
        )

    def detect_storage_signed_integer_arrays(
        self, contract: Contract
    ) -> Set[Tuple[Function, Node]]:
        """
        Detects and returns all nodes with storage-allocated signed integer array init/assignment
        :param contract: Contract to detect within
        :return: A list of tuples with (function, node) where function node has storage-allocated signed integer array init/assignment
        """
        # Create our result set.
        results: Set[Tuple[Function, Node]] = set()

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

    def _detect(self) -> List[Output]:
        """
        Detect storage signed integer array init/assignment
        """
        results = []
        for contract in self.contracts:
            storage_signed_integer_arrays = self.detect_storage_signed_integer_arrays(contract)
            for function, node in storage_signed_integer_arrays:
                contract_info: DETECTOR_INFO = ["Contract ", contract, " \n"]
                function_info: DETECTOR_INFO = ["\t- Function ", function, "\n"]
                node_info: DETECTOR_INFO = [
                    "\t\t- ",
                    node,
                    " has a storage signed integer array assignment\n",
                ]
                res = self.generate_result(contract_info + function_info + node_info)
                results.append(res)

        return results
