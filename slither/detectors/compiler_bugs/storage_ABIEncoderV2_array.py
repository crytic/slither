"""
Module detecting ABIEncoderV2 array bug
"""
from typing import List, Set, Tuple
from slither.detectors.abstract_detector import (
    AbstractDetector,
    DetectorClassification,
    make_solc_versions,
    DETECTOR_INFO,
)
from slither.core.solidity_types import ArrayType
from slither.core.solidity_types import UserDefinedType
from slither.core.variables.local_variable import LocalVariable
from slither.core.variables.state_variable import StateVariable
from slither.slithir.operations import SolidityCall
from slither.core.declarations.solidity_variables import SolidityFunction
from slither.slithir.operations import EventCall
from slither.slithir.operations import HighLevelCall
from slither.utils.utils import unroll
from slither.core.cfg.node import Node
from slither.core.declarations.contract import Contract
from slither.core.declarations.function_contract import FunctionContract
from slither.utils.output import Output


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
    WIKI_DESCRIPTION = """`solc` versions `0.4.7`-`0.5.9` contain a [compiler bug](https://blog.ethereum.org/2019/06/25/solidity-storage-array-bugs) leading to incorrect ABI encoder usage."""

    # region wiki_exploit_scenario
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
    # endregion wiki_exploit_scenario

    WIKI_RECOMMENDATION = "Use a compiler >= `0.5.10`."

    VULNERABLE_SOLC_VERSIONS = make_solc_versions(4, 7, 25) + make_solc_versions(5, 0, 9)

    @staticmethod
    def _detect_storage_abiencoderv2_arrays(
        contract: Contract,
    ) -> Set[Tuple[FunctionContract, Node]]:
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

    def _detect(self) -> List[Output]:
        """
        Detect ABIEncoderV2 array bug
        """
        results = []

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
                info: DETECTOR_INFO = [
                    "Function ",
                    function,
                    " trigger an abi encoding bug:\n\t- ",
                    node,
                    "\n",
                ]
                res = self.generate_result(info)
                results.append(res)

        return results
