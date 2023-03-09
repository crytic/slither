from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.core.solidity_types.function_type import FunctionType

class DoubleRequireCheck(AbstractDetector):
    """
    Gas: Using double require rather than && operator saves gas.
    """

    ARGUMENT = "double-require-check"
    HELP = "Replace && with double require to save gas."
    IMPACT = DetectorClassification.OPTIMIZATION
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = "https://github.com/demis1997/slither-gas-optimizer-detector/wiki/Solidity-Gas-Optimizations-and-Tricks#use-double-require-instead-of-operator-"
    WIKI_TITLE = "Use Double Require Instead of Operator &&"
    WIKI_DESCRIPTION = "Usage of double require will save you around 10 gas with the optimizer enabled."

    def init(self, slither):
        super().init(slither)
        self.issues = {}

    def _detect(self):
        for contract in self.slither.contracts:
            for function in contract.functions:
                if function.function_type == FunctionType.FUNCTION:
                    for block in function.blocks:
                        for instruction in block.instructions:
                            if instruction.asm.startswith("require") and "&&" in instruction.asm:
                                self.issues["{} in {}".format(function.name, contract.name)] = {
                                    "description": "Use double require instead of && operator to save gas."
                                }
        return self.issues