"""
    Module detecting dangerous strict equality

"""
from typing import Any, Dict, List, Union
from slither.analyses.data_dependency.data_dependency import is_dependent_ssa
from slither.core.declarations import Function
from slither.core.declarations.function_top_level import FunctionTopLevel
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.slithir.operations import (
    Assignment,
    Binary,
    BinaryType,
    HighLevelCall,
    SolidityCall,
)

from slither.core.solidity_types import MappingType, ElementaryType

from slither.core.variables.state_variable import StateVariable
from slither.core.declarations.solidity_variables import (
    SolidityVariable,
    SolidityVariableComposed,
    SolidityFunction,
)
from slither.core.cfg.node import Node
from slither.core.declarations.contract import Contract
from slither.core.declarations.function_contract import FunctionContract
from slither.slithir.operations.operation import Operation
from slither.slithir.variables.constant import Constant
from slither.slithir.variables.local_variable import LocalIRVariable
from slither.slithir.variables.temporary_ssa import TemporaryVariableSSA
from slither.utils.output import Output
from slither.utils.type import is_underlying_type_address


class IncorrectStrictEquality(AbstractDetector):
    ARGUMENT = "incorrect-equality"
    HELP = "Dangerous strict equalities"
    IMPACT = DetectorClassification.MEDIUM
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = (
        "https://github.com/crytic/slither/wiki/Detector-Documentation#dangerous-strict-equalities"
    )

    WIKI_TITLE = "Dangerous strict equalities"
    WIKI_DESCRIPTION = "Use of strict equalities that can be easily manipulated by an attacker."

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """
```solidity
contract Crowdsale{
    function fund_reached() public returns(bool){
        return this.balance == 100 ether;
    }
```
`Crowdsale` relies on `fund_reached` to know when to stop the sale of tokens.
`Crowdsale` reaches 100 Ether. Bob sends 0.1 Ether. As a result, `fund_reached` is always false and the `crowdsale` never ends."""
    # endregion wiki_exploit_scenario

    WIKI_RECOMMENDATION = (
        """Don't use strict equality to determine if an account has enough Ether or tokens."""
    )

    sources_taint = [
        SolidityVariable("now"),
        SolidityVariableComposed("block.number"),
        SolidityVariableComposed("block.timestamp"),
    ]

    @staticmethod
    def is_direct_comparison(ir: Operation) -> bool:
        return isinstance(ir, Binary) and ir.type == BinaryType.EQUAL

    @staticmethod
    def is_not_comparing_addresses(ir: Binary) -> bool:
        """
        Comparing addresses strictly should not be flagged.
        """

        if is_underlying_type_address(ir.variable_left.type) and is_underlying_type_address(
            ir.variable_right.type
        ):
            return False

        return True

    @staticmethod
    def is_any_tainted(
        variables: List[
            Union[
                Constant,
                LocalIRVariable,
                TemporaryVariableSSA,
                SolidityVariableComposed,
                SolidityVariable,
            ]
        ],
        taints: List[
            Union[LocalIRVariable, SolidityVariable, SolidityVariableComposed, TemporaryVariableSSA]
        ],
        function: FunctionContract,
    ) -> bool:
        return any(
            (
                is_dependent_ssa(var, taint, function.contract)
                for var in variables
                for taint in taints
            )
        )

    def taint_balance_equalities(
        self, functions: List[Union[FunctionContract, Any]]
    ) -> List[Union[LocalIRVariable, TemporaryVariableSSA, Any]]:
        taints = []
        for func in functions:
            for node in func.nodes:
                for ir in node.irs_ssa:
                    if isinstance(ir, SolidityCall) and ir.function == SolidityFunction(
                        "balance(address)"
                    ):
                        taints.append(ir.lvalue)
                    if isinstance(ir, HighLevelCall):
                        if (
                            isinstance(ir.function, Function)
                            and ir.function.full_name == "balanceOf(address)"
                        ):
                            taints.append(ir.lvalue)
                        if (
                            isinstance(ir.function, StateVariable)
                            and isinstance(ir.function.type, MappingType)
                            and ir.function.name == "balanceOf"
                            and ir.function.type.type_from == ElementaryType("address")
                            and ir.function.type.type_to == ElementaryType("uint256")
                        ):
                            taints.append(ir.lvalue)
                    if isinstance(ir, Assignment):
                        if ir.rvalue in self.sources_taint:
                            taints.append(ir.lvalue)
        return taints

    # Retrieve all tainted (node, function) pairs
    def tainted_equality_nodes(
        self,
        funcs: List[Union[FunctionContract, Any]],
        taints: List[Union[LocalIRVariable, TemporaryVariableSSA, Any]],
    ) -> Dict[FunctionContract, List[Node]]:
        results = {}
        taints += self.sources_taint

        for func in funcs:
            # Disable the detector on top level function until we have good taint on those
            if isinstance(func, FunctionTopLevel):
                continue
            for node in func.nodes:
                for ir in node.irs_ssa:

                    # Filter to only tainted equality (==) comparisons
                    if (
                        self.is_direct_comparison(ir)
                        # Filter out address comparisons which may occur due to lack of field sensitivity in data dependency
                        and self.is_not_comparing_addresses(ir)
                        and self.is_any_tainted(ir.used, taints, func)
                    ):
                        if func not in results:
                            results[func] = []
                        results[func].append(node)

        return results

    def detect_strict_equality(self, contract: Contract) -> Dict[FunctionContract, List[Node]]:
        funcs = contract.all_functions_called + contract.modifiers

        # Taint all BALANCE accesses
        taints = self.taint_balance_equalities(funcs)

        # Accumulate tainted (node,function) pairs involved in strict equality (==) comparisons
        results = self.tainted_equality_nodes(funcs, taints)

        return results

    def _detect(self) -> List[Output]:
        results = []

        for c in self.compilation_unit.contracts_derived:
            ret = self.detect_strict_equality(c)

            # sort ret to get deterministic results
            ret = sorted(list(ret.items()), key=lambda x: x[0].name)
            for f, nodes in ret:

                func_info = [f, " uses a dangerous strict equality:\n"]

                # sort the nodes to get deterministic results
                nodes.sort(key=lambda x: x.node_id)

                # Output each node with the function info header as a separate result.
                for node in nodes:
                    node_info = func_info + ["\t- ", node, "\n"]

                    res = self.generate_result(node_info)
                    results.append(res)

        return results
