"""
Gas: The increment in the for loop post condition can be made unchecked

"""
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.analyses.data_dependency.data_dependency import is_tainted

class GasInefficientLoopCheck(AbstractDetector):
    """
    Gas: Checked variable increment
    """

    ARGUMENT = "gas-checked-increment-for-loop"
    HELP = "The increment in the for loop post condition can be made unchecked"
    IMPACT = DetectorClassification.OPTIMIZATION
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = "https://github.com/demis1997/slither-gas-optimizer-detector/wiki/Solidity-Gas-Optimizations-and-Tricks#the-increment-in-the-for-loops-post-condition-can-be-made-unchecked"
    WIKI_TITLE = "The increment in the for loops post condition can be made unchecked"
    WIKI_DESCRIPTION = "Overflow checks are made by the compiler and you can use unchecked within the for loop to save gas" 
  
    def _check_for_loop(self, node):
        if not node.for_type:
            return False

        increment_op = node.for_type.op
        if increment_op not in ("ADD", "SUB"):
            return False

        increment_variable = node.for_type.left
        if not increment_variable.is_var():
            return False

        if increment_variable.tainted:
            return False

        increment_amount = node.for_type.right
        if not increment_amount.is_constant():
            return False

        increment_value = increment_amount.value
        if increment_op == "SUB":
            increment_value = -increment_value

        for_block = node.statement
        for statement in for_block.statements:
            if statement is increment_variable.definition:
                continue
            if is_tainted(statement, increment_variable):
                return False

        self._results.append((node, f"Unchecked for loop increment: {node.for_type}"))

        return True

    def analyze(self):
        self._results = []
        for node in self.slither.solidity_nodes:
            self._check_for_loop(node)
        return self._results