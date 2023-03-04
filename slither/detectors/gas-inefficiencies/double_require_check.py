from slither.slither import Slither
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.core.solidity_types.function_type import FunctionType
from slither.core.solidity_types.elementary_type import ElementaryType

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

    def check(self):
        double_requires_found = False
        for contract in self.slither.contracts:
            for function in contract.functions:
                if function.function_type == FunctionType.FUNCTION:
                    for block in function.blocks:
                        for instruction in block.instructions:
                            if instruction.asm.startswith("require") and "&&" in instruction.asm:
                                self.log("Double require found in {} function in contract {}".format(function.name, contract.name))
                                double_requires_found = True


if __name__ == "__main__":
    slither = Slither(".")
    detector = DoubleRequireCheck(slither)
    detector.run()

" use slither double_require_check.py"