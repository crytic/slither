from slither.core.solidity_types.elementary_type import ElementaryType
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.detectors.abstract_detector import DetectorResult
from slither.detectors.abstract_detector import DetectorSeverity
from slither.detectors.abstract_detector import DetectorType
from slither.slithir.operations import Operation
from slither  import Lt, Gt
from slither import Not

class InefficientInequalityDetector(AbstractDetector):
    
    WIKI = "https://github.com/demis1997/slither-gas-optimizer-detector/wiki/Solidity-Gas-Optimizations-and-Tricks#-is-cheaper-than-"
    WIKI_TITLE = ">= is cheaper than >"
    WIKI_DESCRIPTION = "Non-strict inequalities (>=) are cheaper than strict ones (>). Non-strict inequalities will save you 15–20 gas."
    IMPACT = DetectorClassification.OPTIMIZATION
    CONFIDENCE = DetectorClassification.MEDIUM

    def __init__(self, contracts):
        self.contracts = contracts
        self.results = {}

    def analyze(self):
        for contract in self.contracts:
            for function in contract.functions:
                for block in function.blocks:
                    for operation in block.operations:
                        if isinstance(operation, (Lt, Gt)):
                            if isinstance(operation.left, Operation) or isinstance(operation.right, Operation):
                                continue
                            if isinstance(operation.left, Not) or isinstance(operation.right, Not):
                                continue
                            if isinstance(operation.left.typ, (bool, ElementaryType)) and isinstance(operation.right.typ, (bool, ElementaryType)):
                                continue
                            if isinstance(operation.left.typ, ElementaryType) and isinstance(operation.right.typ, ElementaryType) and operation.left.typ != operation.right.typ:
                                continue
                            self.results[contract.name].append(DetectorResult(
                                DetectorType.PERFORMANCE,
                                f"Contract {contract.name} in function {function.name} uses an inefficient inequality operator: {operation.print()}",
                                DetectorSeverity.MEDIUM,
                                DetectorClassification.INFO
                            ))

    def get_results(self):
        return self.results
