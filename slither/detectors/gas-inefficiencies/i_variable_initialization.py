from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.analyses.data_dependency.data_dependency import is_tainted

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

    def _detect(self):
        issues = {}
        for function in self.contract.functions:
            for node in function.nodes:
                if node.type == "for":
                    for init in node.init:
                        if init.assignment_operation and init.assignment_operation.target_elementary_type.name == "uint256":
                            variable = init.assignment_operation.left_element
                            if not is_tainted(init.assignment_operation.right, {"tainted": []}, {"tainted": [variable]}):
                                issue = {"variable": variable.name, "node": node.src_code, "lineno": node.lineno}
                                if function.name not in issues:
                                    issues[function.name] = []
                                issues[function.name].append(issue)
        return issues
