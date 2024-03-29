"""
Module detecting modifiers that are not guaranteed to execute _; or revert()/throw

Note that require()/assert() are not considered here. Even if they
are in the outermost scope, they do not guarantee a revert, so a
default value can still be returned.
"""
import json
import json
from slither.core.declarations.solidity_variables import SolidityVariableComposed
from slither.core.expressions import CallExpression
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
            
    
            
class CentralizedRiskLOW(AbstractDetector):
    """
    Detector for modifiers that return a default value
    """

    ARGUMENT = "centralized-risk-low"
    HELP = "Modifiers that can return the default value"
    IMPACT = DetectorClassification.LOW
    CONFIDENCE = DetectorClassification.HIGH
    WIKI = " "

    WIKI_TITLE = "Centralized Risk"
    WIKI_DESCRIPTION = "aaa"

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """
If the condition in `myModif` is false, the execution of `get()` will return 0."""
    # endregion wiki_exploit_scenario

    WIKI_RECOMMENDATION = "All the paths in a modifier must execute `_` or revert."

    def _detect(self):
        '''
        This function is used to detect the centralized risk in the contract
        '''
        results = []
        contract_info=[]

        for c in self.contracts:
            # contract_info = ["centralized risk found in", c, '\n']
            for function in c.functions:
                if function.name.lower() in ["transfer","transferfrom"]:
                    continue
                if CentralizedUtil.check_if_state_vars_read_from_critical_risk(function):
                    if function.visibility in ["public", "external"] and not function.view:
                        centralized_info_functions = CentralizedUtil.detect_function_if_centralized(function)
                        for centralized_info_function in centralized_info_functions:
                            if centralized_info_function['oz_read_or_written'] or \
                                    centralized_info_function['function_modifier_info']:
                                function_info = CentralizedUtil.output_function_centralized_info(function)
                                contract_info.append(self.generate_result(["\t- ", function, "\n"]))
        results.extend(contract_info) if contract_info else None
        return results
        
