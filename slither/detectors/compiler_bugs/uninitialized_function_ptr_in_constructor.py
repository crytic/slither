"""
Module detecting uninitialized function pointer calls in constructors
"""
from typing import Any, List, Union
from slither.detectors.abstract_detector import (
    AbstractDetector,
    DetectorClassification,
    make_solc_versions,
    DETECTOR_INFO,
)
from slither.slithir.operations import InternalDynamicCall, OperationWithLValue
from slither.slithir.variables import ReferenceVariable
from slither.slithir.variables.variable import SlithIRVariable
from slither.core.cfg.node import Node
from slither.core.declarations.contract import Contract
from slither.core.declarations.function_contract import FunctionContract
from slither.slithir.variables.state_variable import StateIRVariable
from slither.utils.output import Output


def _get_variables_entrance(function: FunctionContract) -> List[Union[Any, StateIRVariable]]:
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


def _is_vulnerable(node: Node, variables_entrance: List[Union[Any, StateIRVariable]]) -> bool:
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

    VULNERABLE_SOLC_VERSIONS = make_solc_versions(4, 5, 25) + make_solc_versions(5, 0, 8)

    @staticmethod
    def _detect_uninitialized_function_ptr_in_constructor(
        contract: Contract,
    ) -> List[Union[Any, Node]]:
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

    def _detect(self) -> List[Output]:
        """
        Detect uninitialized function pointer calls in constructors of contracts
        Returns:
            list: ['uninitialized function pointer calls in constructors']
        """
        results = []

        for contract in self.compilation_unit.contracts:
            contract_info: DETECTOR_INFO = ["Contract ", contract, " \n"]
            nodes = self._detect_uninitialized_function_ptr_in_constructor(contract)
            for node in nodes:
                node_info: DETECTOR_INFO = [
                    "\t ",
                    node,
                    " is an unintialized function pointer call in a constructor\n",
                ]
                json = self.generate_result(contract_info + node_info)
                results.append(json)

        return results
