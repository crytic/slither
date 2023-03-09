from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.slithir.operations import Operation

class GasShiftOperatorCheck(AbstractDetector):
    """
    Gas: Using shift operators as opposed to multiplication/division operators where possible will save gas.
    """

    ARGUMENT = "shift-operators-check"
    HELP = "Shift operators can be used in place of multiplication or division operators where possible."
    IMPACT = DetectorClassification.OPTIMIZATION
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = "https://github.com/demis1997/slither-gas-optimizer-detector/wiki/Solidity-Gas-Optimizations-and-Tricks#use-shift-rightleft-instead-of-divisionmultiplication-if-possible"
    WIKI_TITLE = "Use Shift Right/Left instead of Division/Multiplication if possible"
    WIKI_DESCRIPTION = "A division/multiplication by any number x being a power of 2 can be calculated by shifting log2(x) to the right or left."

    def _detect(self):
        results = {}
        # get all arithmetic operations
        for contract in self.slither.contracts:
            for function in contract.functions:
                for node in function.nodes:
                    if isinstance(node, Operation):
                        if node.operator == '*' or node.operator == '/':
                            if isinstance(node.left, ElementaryType) and isinstance(node.right, ElementaryType):
                                if self.is_power_of_two(node.right):
                                    results[node] = {'description': 'Consider using shift operator instead of multiplication/division.', 'severity': 'medium'}
        return results
    
    def is_power_of_two(self, n):
        """Returns True if n is a power of 2."""
        return (n & (n - 1) == 0) and n != 0
