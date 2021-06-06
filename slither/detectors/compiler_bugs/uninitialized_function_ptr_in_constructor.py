"""
Module detecting uninitialized function pointer calls in constructors
"""

from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.slithir.operations import InternalDynamicCall, OperationWithLValue
from slither.slithir.variables import ReferenceVariable
from slither.slithir.variables.variable import SlithIRVariable

vulnerable_solc_versions = [
    "0.4.5",
    "0.4.6",
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
]


def _get_variables_entrance(function):
    """
    Return the first SSA variables of the function
    Catpure the phi operation at the entry point
    """
    ret = []
    if function.entry_point:
        for ir_ssa in function.entry_point.irs_ssa:
            if isinstance(ir_ssa, OperationWithLValue):
                ret.append(ir_ssa.lvalue)
    return ret


def _is_vulnerable(node, variables_entrance):
    """
    Vulnerable if an IR ssa:
        - It is an internal dynamic call
        - The destination has not an index of 0
        - The destination is not in the allowed variable
    """
    for ir_ssa in node.irs_ssa:
        if isinstance(ir_ssa, InternalDynamicCall):
            destination = ir_ssa.function
            # If it is a reference variable, destination should be the origin variable
            # Note: this will create FN if one of the field of a structure is updated, while not begin
            # the field of the function pointer. This should be fixed once we have the IR refactoring
            if isinstance(destination, ReferenceVariable):
                destination = destination.points_to_origin
            if isinstance(destination, SlithIRVariable) and ir_ssa.function.index == 0:
                return True
            if destination in variables_entrance:
                return True
    return False


class UninitializedFunctionPtrsConstructor(AbstractDetector):
    """
    Uninitialized function pointer calls in constructors
    """

    ARGUMENT = "uninitialized-fptr-cst"
    HELP = "Uninitialized function pointer calls in constructors"
    IMPACT = DetectorClassification.LOW
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#uninitialized-function-pointers-in-constructors"
    WIKI_TITLE = "Uninitialized function pointers in constructors"
    WIKI_DESCRIPTION = "solc versions `0.4.5`-`0.4.26` and `0.5.0`-`0.5.8` contain a compiler bug leading to unexpected behavior when calling uninitialized function pointers in constructors."

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """
```solidity
contract bad0 {

  constructor() public {
    /* Uninitialized function pointer */
    function(uint256) internal returns(uint256) a;
    a(10);
  }

}
```
The call to `a(10)` will lead to unexpected behavior because function pointer `a` is not initialized in the constructor."""
    # endregion wiki_exploit_scenario

    WIKI_RECOMMENDATION = (
        "Initialize function pointers before calling. Avoid function pointers if possible."
    )

    @staticmethod
    def _detect_uninitialized_function_ptr_in_constructor(contract):
        """
        Detect uninitialized function pointer calls in constructors
        :param contract: The contract of interest for detection
        :return: A list of nodes with uninitialized function pointer calls in the constructor of given contract
        """
        results = []
        constructor = contract.constructors_declared
        if constructor:
            variables_entrance = _get_variables_entrance(constructor)
            results = [
                node for node in constructor.nodes if _is_vulnerable(node, variables_entrance)
            ]
        return results

    def _detect(self):
        """
        Detect uninitialized function pointer calls in constructors of contracts
        Returns:
            list: ['uninitialized function pointer calls in constructors']
        """
        results = []

        # Check if vulnerable solc versions are used
        if self.compilation_unit.solc_version not in vulnerable_solc_versions:
            return results

        for contract in self.compilation_unit.contracts:
            contract_info = ["Contract ", contract, " \n"]
            nodes = self._detect_uninitialized_function_ptr_in_constructor(contract)
            for node in nodes:
                node_info = [
                    "\t ",
                    node,
                    " is an unintialized function pointer call in a constructor\n",
                ]
                json = self.generate_result(contract_info + node_info)
                results.append(json)

        return results
