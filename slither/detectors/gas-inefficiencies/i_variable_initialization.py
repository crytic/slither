from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.slithir.operations import VariableIncrements
from slither.analyses.data_dependency.data_dependency import is_tainted
from slither.core.solidity_types.elementary_type import ElementaryType

class GasIVariableInitCheck(AbstractDetector):
    """
    Gas: Not initializing the i variable in a for loop will not save gas; it might take up more.
    """

    ARGUMENT = "i-variable-initialization"
    HELP = "The i variable should still be initialized in the for loop."
    IMPACT = DetectorClassification.OPTIMIZATION
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = "https://github.com/demis1997/slither-gas-optimizer-detector/wiki/Solidity-Gas-Optimizations-and-Tricks#dont-remove-the-initialization-of-i-variable-in-for-loops"
    WIKI_TITLE = "Don't remove the initialization of i variable in for loops"
    WIKI_DESCRIPTION = "Removing the i variable initialization to outside of the loop is thought to save gas; it does not, and should remain within the for loop."

    def analyze(self):
        for function in self.contract.functions:
            for node in function.nodes:
                if node.type == "for":
                    for init in node.init:
                        if isinstance(init, VariableIncrements):
                            variable = init.variable
                            if isinstance(variable.type, ElementaryType) and variable.type.name == "uint256":
                                if not is_tainted(init.operand, {"tainted": []}, {"tainted": [variable]}):
                                    self._issues.append({"variable": variable.name, "node": node.src_code, "lineno": node.lineno})

                                    "run slither <path-to-contract> GasIVariableInitCheck"