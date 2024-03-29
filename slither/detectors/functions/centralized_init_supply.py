"""
Module detecting modifiers that are not guaranteed to execute _; or revert()/throw

Note that require()/assert() are not considered here. Even if they
are in the outermost scope, they do not guarantee a revert, so a
default value can still be returned.
"""
import json
from slither.core.declarations.solidity_variables import SolidityVariableComposed
from slither.core.expressions import CallExpression
from slither.core.variables.state_variable import StateVariable
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.core.cfg.node import NodeType
from slither.core.declarations import (
    Contract,
    Pragma,
    Import,
    Function,
    Modifier,
)
from slither.core.declarations.event import Event
from slither.core.declarations import FunctionContract, Modifier
from slither.core.declarations import (
    SolidityFunction,
)
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.detectors.functions.centralized_utils import CentralizedUtil

from slither.slithir.operations import SolidityCall,InternalCall
from slither.slithir.operations.binary import Binary
from slither.slithir.operations.index import Index
from slither.slithir.operations.binary import BinaryType
from slither.detectors.functions.modifier_utils import ModifierUtil
            
    

            
class CentralizedInitSupply(AbstractDetector):
    """
    Detector for modifiers that return a default value
    """

    ARGUMENT = "centralized-init-supply"
    HELP = "centrlized risk with supply totalsupply token in constructor during initial the contract"
    IMPACT = DetectorClassification.INFORMATIONAL
    CONFIDENCE = DetectorClassification.HIGH
    WIKI = " "

    WIKI_TITLE = "Centralized Risk with supply"
    WIKI_DESCRIPTION = "centrlized risk with supply totalsupply token in constructor during initial the contract"

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """
    centrlized risk with supply totalsupply token in constructor during initial the contract """
    # endregion wiki_exploit_scenario

    WIKI_RECOMMENDATION = "centrlized risk with supply totalsupply token in constructor during initial the contract"

    def _detect(self):
        
        results = []
        for c in self.contracts:
            if c.constructor:
                for node in c.constructor.nodes:
                    if "mint" in str(node).lower():
                        contract_info = ["centralized risk found in ", node, 'which has a token supply distribution in constructor \n']
                        res = self.generate_result(contract_info)
                        results.append(res)
                    if len(node.variables_written)>0:
                        if any(isinstance(var_written,StateVariable) and var_written.full_name.lower() in ["balances(address)","_balances(address)","_rowned(address)"] for var_written in node.variables_written):
                            contract_info = ["centralized risk found in ", node, 'which has a token supply distribution in constructor \n']
                            res = self.generate_result(contract_info)
                            results.append(res)
            for f in c.functions:
                if "init" in f.name.lower():
                    for node in f.nodes: 
                        if "mint" in str(node).lower():
                            contract_info = ["centralized risk found in ", node, 'which has a token supply distribution in constructor \n']
                            res = self.generate_result(contract_info)
                            results.append(res)
                        if len(node.variables_written)>0:
                            if any(isinstance(var_written,StateVariable) and var_written.full_name.lower() in ["balances(address)","_balances(address)","_rowned(address)"] for var_written in node.variables_written):
                                contract_info = ["centralized risk found in ", node, 'which has a token supply distribution in constructor \n']
                                res = self.generate_result(contract_info)
                                results.append(res)

        return results
        
