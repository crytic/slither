from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.analyses.data_dependency.data_dependency import DataDependency
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.slithir.operations import BinaryOperation

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

    def _evaluate(self):
        # get all arithmetic operations
        data_dependency = DataDependency(self.contract)
        arithmetic_operations = data_dependency.get_arithmetic_operations()

        # check if each operation can be replaced by shift operator
        for op in arithmetic_operations:
            if isinstance(op, BinaryOperation):
                if op.operator == '*' or op.operator == '/':
                    if isinstance(op.left, ElementaryType) and isinstance(op.right, ElementaryType):
                        if self.is_power_of_two(op.right):
                            self._issues.append({'variable': op, 'description': 'Consider using shift operator instead of multiplication/division.', 'severity': 'medium'})
                
    def is_power_of_two(self, n):
        """Returns True if n is a power of 2."""
        return (n & (n - 1) == 0) and n != 0
