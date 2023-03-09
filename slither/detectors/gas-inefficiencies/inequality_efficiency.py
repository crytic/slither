from slither.core.solidity_types.elementary_type import ElementaryType
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification

class InefficientInequalityDetector(AbstractDetector):
    ARGUMENT = "inefficient-inequality-detector"
    HELP = "Checks for the use of an inefficient inequality operator."
    IMPACT = DetectorClassification.OPTIMIZATION
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = "https://github.com/demis1997/slither-gas-optimizer-detector/wiki/Solidity-Gas-Optimizations-and-Tricks#-is-cheaper-than-"
    WIKI_TITLE = ">= is cheaper than >"
    WIKI_DESCRIPTION = "Non-strict inequalities (>=) are cheaper than strict ones (>). Non-strict inequalities will save you 15–20 gas."

    def __init__(self, contracts):
        super().__init__(contracts)
        self.issues = {}

    def _detect(self):
        for contract in self.contracts:
            self.issues[contract.name] = []
            for function in contract.functions:
                for block in function.blocks:
                    for operation in block.operations:
                        if type(operation).__name__ in ["Lt", "Gt"]:
                            if type(operation.left).__name__ == "Operation" or type(operation.right).__name__ == "Operation":
                                continue
                            if type(operation.left).__name__ == "Not" or type(operation.right).__name__ == "Not":
                                continue
                            if isinstance(operation.left.typ, (bool, ElementaryType)) and isinstance(operation.right.typ, (bool, ElementaryType)):
                                continue
                            if isinstance(operation.left.typ, ElementaryType) and isinstance(operation.right.typ, ElementaryType) and operation.left.typ != operation.right.typ:
                                continue
                            self.issues[contract.name].append({
                                "type": "PERFORMANCE",
                                "message": "Contract {0} in function {1} uses an inefficient inequality operator: {2}".format(contract.name, function.name, operation.print()),
                                "severity": "MEDIUM",
                                "classification": "INFO",
                                "location": {"filename": contract.name, "lineno": operation.lineno}
                            })

    def get_issues(self):
        return self.issues
