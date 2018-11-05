"""
    Module detecting send to arbitrary address

    To avoid FP, it does not report:
        - If msg.sender is used as index (withdraw situation)
        - If the function is protected
        - If the value sent is msg.value (repay situation)

    TODO: dont report if the value is tainted by msg.value
"""

from slither.analyses.taint.calls import KEY
from slither.analyses.taint.calls import run_taint as run_taint_calls
from slither.analyses.taint.specific_variable import is_tainted
from slither.analyses.taint.specific_variable import \
    run_taint as run_taint_variable
from slither.core.declarations.solidity_variables import (SolidityFunction,
                                                          SolidityVariableComposed)
from slither.detectors.abstract_detector import (AbstractDetector,
                                                 DetectorClassification)
from slither.slithir.operations import (HighLevelCall, Index, LowLevelCall,
                                        Send, SolidityCall, Transfer)


class ArbitrarySend(AbstractDetector):
    """
    """

    ARGUMENT = 'arbitrary-send'
    HELP = 'Functions that send ether to arbitrary destinations'
    IMPACT = DetectorClassification.HIGH
    CONFIDENCE = DetectorClassification.MEDIUM

    @staticmethod
    def arbitrary_send(func):
        """
        """
        if func.is_protected():
            return []

        ret = []
        for node in func.nodes:
            for ir in node.irs:
                if isinstance(ir, SolidityCall):
                    if ir.function == SolidityFunction('ecrecover(bytes32,uint8,bytes32,bytes32)'):
                        return False
                if isinstance(ir, Index):
                    if ir.variable_right == SolidityVariableComposed('msg.sender'):
                        return False
                    if is_tainted(ir.variable_right, SolidityVariableComposed('msg.sender')):
                        return False
                if isinstance(ir, (HighLevelCall, LowLevelCall, Transfer, Send)):
                    if ir.call_value is None:
                        continue
                    if ir.call_value == SolidityVariableComposed('msg.value'):
                        continue
                    if is_tainted(ir.call_value, SolidityVariableComposed('msg.value')):
                        continue

                    if KEY in ir.context:
                        if ir.context[KEY]:
                            ret.append(node)
        return ret


    def detect_arbitrary_send(self, contract):
        """
            Detect arbitrary send
        Args:
            contract (Contract)
        Returns:
            list((Function), (list (Node)))
        """
        ret = []
        for f in [f for f in contract.functions if f.contract == contract]:
            nodes = self.arbitrary_send(f)
            if nodes:
                ret.append((f, nodes))
        return ret

    def detect(self):
        """
        """
        results = []

        # Look if the destination of a call is tainted
        run_taint_calls(self.slither)

        # Taint msg.value
        taint = SolidityVariableComposed('msg.value')
        run_taint_variable(self.slither, taint)

        # Taint msg.sender
        taint = SolidityVariableComposed('msg.sender')
        run_taint_variable(self.slither, taint)

        for c in self.contracts:
            arbitrary_send = self.detect_arbitrary_send(c)
            for (func, nodes) in arbitrary_send:
                func_name = func.name
                calls_str = [str(node.expression) for node in nodes]

                txt = "Arbitrary send in {} Contract: {}, Function: {}, Calls: {}"
                info = txt.format(self.filename,
                                  c.name,
                                  func_name,
                                  calls_str)

                self.log(info)

                source_mapping = [node.source_mapping for node in nodes]

                results.append({'vuln': 'SuicidalFunc',
                                'sourceMapping': source_mapping,
                                'filename': self.filename,
                                'contract': c.name,
                                'func': func_name,
                                'calls': calls_str})

        return results
