"""
Gas: Module detecting Array length inside of loop

"""
from collections import defaultdict
from slither.core.solidity_types.elementary_type import ElementaryType

from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.detectors.abstract_detector import Detection
from slither import CFG
from slither.core.solidity_types import ArrayType
from slither.slithir.operations import Load

class GasInefficientLoopLength(AbstractDetector):
    """
    Gas: Array length inside of loop
    """

    ARGUMENT = "gas-length-within-for-loop"
    HELP = "Gas Inefficiencies Detected"
    IMPACT = DetectorClassification.OPTIMIZATION
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = "https://github.com/demis1997/slither-gas-optimizer-detector/wiki/Solidity-Gas-Optimizations-and-Tricks#caching-the-length-in-for-loops"
    WIKI_TITLE = "Caching the length in for loops"
    WIKI_DESCRIPTION = "Reading array length at each iteration of the loop takes 6 gas" 
    
    def check(self):
        results = []
        for contract in self.contracts:
            cfg = CFG(contract)
            for function in contract.functions:
                for block in function.blocks:
                    for instruction in block.instruction_list:
                        if isinstance(instruction, Load) and isinstance(instruction.variable.type, ArrayType):
                            index_op = instruction.index_op
                            if isinstance(index_op, Load) and isinstance(index_op.variable.type, ElementaryType) and cfg.is_loop_header(block):
                                results.append({
                                    "contract": contract.name,
                                    "function": function.name,
                                    "line": instruction.lineno,
                                    "variable": instruction.variable.name
                                })
        return results