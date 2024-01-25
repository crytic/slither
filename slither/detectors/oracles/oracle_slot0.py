from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.core.declarations.contract import Contract
from slither.core.cfg.node import NodeType
from slither.core.declarations.function_contract import FunctionContract
from slither.detectors.oracles.oracle import Oracle


class OracleSlot0(AbstractDetector):
    """
    Documentation
    """

    ARGUMENT = "slot0"  # slither will launch the detector with slither.py --detect mydetector
    HELP = "Help printed by slither"
    IMPACT = DetectorClassification.HIGH
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = "RUN"

    WIKI_TITLE = "asda"
    WIKI_DESCRIPTION = "Slot0 is vulnerable to price manipulation as it gets price at the current moment. TWAP should be used instead."
    WIKI_EXPLOIT_SCENARIO = "asdsad"
    WIKI_RECOMMENDATION = "asdsad"

    oracles = []

    def detect_slot0(self, contracts: Contract):
        """
        Detects off-chain oracle contract and VAR
        """
        self.oracles = []
        for contract in contracts:
            for function in contract.functions:
                if function.is_constructor:
                    continue
                for functionCalled in function.external_calls_as_expressions:
                    if "slot0" in str(functionCalled):
                        self.oracles.append(
                            Oracle(
                                contract,
                                function,
                                str(functionCalled).split(".", maxsplit=1)[0],
                                functionCalled.source_mapping.lines[0],
                            )
                        )

    def _detect(self):
        results = []
        self.detect_slot0(self.contracts)
        # for oracle in self.oracles:
        #     print(oracle.contract.name, oracle.function.name)
        for oracle in self.oracles:
            results.append(
                "Slot0 usage found in contract "
                + oracle.contract.name
                + " in function "
                + oracle.function.name
            )
            results.append("\n")
        res = self.generate_result(results)
        output = []
        output.append(res)
        return output
