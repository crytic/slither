"""
Module detecting ABIEncoderV2 array bug
"""

from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.core.solidity_types import ArrayType
from slither.core.solidity_types import UserDefinedType
from slither.core.variables.local_variable import LocalVariable
from slither.core.variables.state_variable import StateVariable
from slither.slithir.operations import SolidityCall
from slither.core.declarations.solidity_variables import SolidityFunction
from slither.slithir.operations import EventCall
from slither.slithir.operations import HighLevelCall
from slither.utils.utils import unroll

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


class ABIEncoderV2Array(AbstractDetector):
    """
    Detects Storage ABIEncoderV2 array bug
    """

    ARGUMENT = "abiencoderv2-array"
    HELP = "Storage abiencoderv2 array"
    IMPACT = DetectorClassification.HIGH
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = (
        "https://github.com/crytic/slither/wiki/Detector-Documentation#storage-abiencoderv2-array"
    )
    WIKI_TITLE = "Storage ABIEncoderV2 Array"
    WIKI_DESCRIPTION = """`solc` versions `0.4.7`-`0.5.10` contain a [compiler bug](https://blog.ethereum.org/2019/06/25/solidity-storage-array-bugs.) leading to incorrect ABI encoder usage."""
    WIKI_EXPLOIT_SCENARIO = """
```solidity
contract A {
    uint[2][3] bad_arr = [[1, 2], [3, 4], [5, 6]];
    
    /* Array of arrays passed to abi.encode is vulnerable */
    function bad() public {                                                                                          
        bytes memory b = abi.encode(bad_arr);
    }
}
```
`abi.encode(bad_arr)` in a call to `bad()` will incorrectly encode the array as `[[1, 2], [2, 3], [3, 4]]` and lead to unintended behavior.
"""
    WIKI_RECOMMENDATION = "Use a compiler >= `0.5.10`."

    @staticmethod
    def _detect_storage_abiencoderv2_arrays(contract):
        """
        Detects and returns all nodes with storage-allocated abiencoderv2 arrays of arrays/structs in abi.encode, events or external calls
        :param contract: Contract to detect within
        :return: A list of tuples with (function, node) where function node has storage-allocated abiencoderv2 arrays of arrays/structs
        """
        # Create our result set.
        results = set()

        # Loop for each function and modifier.
        # pylint: disable=too-many-nested-blocks
        for function in contract.functions_and_modifiers_declared:
            # Loop every node, looking for storage-allocated array of arrays/structs
            # in arguments to abi.encode, events or external calls
            for node in function.nodes:
                for ir in node.irs:
                    # Call to abi.encode()
                    if (
                        isinstance(ir, SolidityCall)
                        and ir.function == SolidityFunction("abi.encode()")
                        or
                        # Call to emit event
                        # Call to external function
                        isinstance(ir, (EventCall, HighLevelCall))
                    ):
                        for arg in unroll(ir.arguments):
                            # Check if arguments are storage allocated arrays of arrays/structs
                            if (
                                isinstance(arg.type, ArrayType)
                                # Storage allocated
                                and (
                                    isinstance(arg, StateVariable)
                                    or (isinstance(arg, LocalVariable) and arg.is_storage)
                                )
                                # Array of arrays or structs
                                and isinstance(arg.type.type, (ArrayType, UserDefinedType))
                            ):
                                results.add((function, node))
                                break

        # Return the resulting set of tuples
        return results

    def _detect(self):
        """
        Detect ABIEncoderV2 array bug
        """
        results = []

        # Check if vulnerable solc versions are used
        if self.compilation_unit.solc_version not in vulnerable_solc_versions:
            return results

        # Check if pragma experimental ABIEncoderV2 is used
        if not any(
            (p.directive[0] == "experimental" and p.directive[1] == "ABIEncoderV2")
            for p in self.compilation_unit.pragma_directives
        ):
            return results

        # Check for storage-allocated abiencoderv2 arrays of arrays/structs
        # in arguments of abi.encode, events or external calls
        for contract in self.contracts:
            storage_abiencoderv2_arrays = self._detect_storage_abiencoderv2_arrays(contract)
            for function, node in storage_abiencoderv2_arrays:
                info = ["Function ", function, " trigger an abi encoding bug:\n\t- ", node, "\n"]
                res = self.generate_result(info)
                results.append(res)

        return results
