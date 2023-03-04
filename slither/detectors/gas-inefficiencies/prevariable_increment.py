"""
Gas: The ++ operator should be written before the variable

"""
from slither.solc_parsing.variables import StateVariable, LocalVariable
from collections import defaultdict
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.analyses.data_dependency.data_dependency import is_tainted
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.slithir.operations import Send, Transfer, LowLevelCall
from slither.slithir.operations import Call



class GasVariableIncrementCheck(AbstractDetector):
    """
    Gas: Variable increments cost less gas if they are before the variable
    """

    ARGUMENT = "gas-pre-variable-increment"
    HELP = "The increment of the variable can be placed before the variable"
    IMPACT = DetectorClassification.OPTIMIZATION
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = "https://github.com/demis1997/slither-gas-optimizer-detector/wiki/Solidity-Gas-Optimizations-and-Tricks#i-costs-less-gas-compared-to-i-or-i--1"
    WIKI_TITLE = "The increment in the for loops post condition can be added before the variable"
    WIKI_DESCRIPTION = "using ++i instead of i++ saves gas" 

    def _detect(self):
        results = defaultdict(list)
        for contract in self.slither.contracts:
            for function in contract.functions:
                for node in function.nodes:
                    if isinstance(node, (Send, Transfer, LowLevelCall, Call)):
                        if is_tainted(node):
                            results[node].append(self.MSG.format(node=node))
                    elif isinstance(node, (StateVariable, LocalVariable)):
                        if "++" in node.name:
                            results[node].append(self.MSG.format(node=node))
        return results