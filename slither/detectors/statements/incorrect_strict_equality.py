"""
    Module detecting dangerous strict equality

"""

import itertools
from slither.analyses.data_dependency.data_dependency import is_dependent_ssa
from slither.core.declarations import Function
from slither.detectors.abstract_detector import (AbstractDetector,
                                                 DetectorClassification)
from slither.slithir.operations import (Assignment, Balance, Binary, BinaryType,
                                        HighLevelCall)

from slither.core.solidity_types import MappingType, ElementaryType

from slither.core.variables.state_variable import StateVariable
from slither.core.declarations.solidity_variables import SolidityVariable, SolidityVariableComposed
from slither.slithir.variables import ReferenceVariable

class IncorrectStrictEquality(AbstractDetector):
    ARGUMENT = 'incorrect-equality'
    HELP = 'Dangerous strict equalities'
    IMPACT = DetectorClassification.MEDIUM
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = 'https://github.com/crytic/slither/wiki/Detector-Documentation#dangerous-strict-equalities'

    WIKI_TITLE = 'Dangerous strict equalities'
    WIKI_DESCRIPTION = 'Use of strict equalities that can be easily manipulated by an attacker.'
    WIKI_EXPLOIT_SCENARIO = '''
```solidity
contract Crowdsale{
    function fund_reached() public returns(bool){
        return this.balance == 100 ether;
    }
```
`Crowdsale` relies on `fund_reached` to know when to stop the sale of tokens. `Crowdsale` reaches 100 ether. Bob sends 0.1 ether. As a result, `fund_reached` is always false and the crowdsale never ends.'''

    WIKI_RECOMMENDATION = '''Don't use strict equality to determine if an account has enough ethers or tokens.'''

    sources_taint = [SolidityVariable('now'),
                     SolidityVariableComposed('block.number'),
                     SolidityVariableComposed('block.timestamp')]

    @staticmethod
    def is_direct_comparison(ir):
        return isinstance(ir, Binary) and ir.type == BinaryType.EQUAL

    @staticmethod
    def is_any_tainted(variables, taints, function):
        return any([is_dependent_ssa(var, taint, function.contract) for var in variables for taint in taints])

    def taint_balance_equalities(self, functions):
        taints = []
        for func in functions:
            for node in func.nodes:
                for ir in node.irs_ssa:
                    if isinstance(ir, Balance):
                        taints.append(ir.lvalue)
                    if isinstance(ir, HighLevelCall):
                        #print(ir.function.full_name)
                        if isinstance(ir.function, Function) and\
                            ir.function.full_name == 'balanceOf(address)':
                                taints.append(ir.lvalue)
                        if isinstance(ir.function, StateVariable) and\
                            isinstance(ir.function.type, MappingType) and\
                            ir.function.name == 'balanceOf' and\
                            ir.function.type.type_from == ElementaryType('address') and\
                            ir.function.type.type_to == ElementaryType('uint256'):
                                taints.append(ir.lvalue)
                    if isinstance(ir, Assignment):
                        if ir.rvalue in self.sources_taint:
                            taints.append(ir.lvalue)

        return taints

    # Retrieve all tainted (node, function) pairs
    def tainted_equality_nodes(self, funcs, taints):
        results = dict()
        taints += self.sources_taint

        for func in funcs:
            for node in func.nodes:
                for ir in node.irs_ssa:

                    # Filter to only tainted equality (==) comparisons
                    if self.is_direct_comparison(ir) and self.is_any_tainted(ir.used, taints, func):
                        if func not in results:
                            results[func] = []
                        results[func].append(node)

        return results

    def detect_strict_equality(self, contract):
        funcs = contract.all_functions_called + contract.modifiers

        # Taint all BALANCE accesses
        taints = self.taint_balance_equalities(funcs)

        # Accumulate tainted (node,function) pairs involved in strict equality (==) comparisons
        results = self.tainted_equality_nodes(funcs, taints)

        return results

    def _detect(self):
        results = []

        for c in self.slither.contracts_derived:
            ret = self.detect_strict_equality(c)

            # sort ret to get deterministic results
            ret = sorted(list(ret.items()), key=lambda x:x[0].name)
            for f, nodes in ret:
                func_info = "{}.{} ({}) uses a dangerous strict equality:\n".format(f.contract.name,
                                                                               f.name,
                                                                               f.source_mapping_str)

                # sort the nodes to get deterministic results
                nodes.sort(key=lambda x: x.node_id)

                # Output each node with the function info header as a separate result.
                for node in nodes:
                    node_info = func_info + f"\t- {str(node.expression)}\n"

                    json = self.generate_json_result(node_info)
                    self.add_node_to_json(node, json)
                    self.add_function_to_json(f, json)
                    results.append(json)

        return results
