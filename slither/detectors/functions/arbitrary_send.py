"""
    Module detecting send to arbitrary address

    To avoid FP, it does not report:
        - If msg.sender is used as index (withdraw situation)
        - If the function is protected
        - If the value sent is msg.value (repay situation)
        - If there is a call to transferFrom

    TODO: dont report if the value is tainted by msg.value
"""
from slither.core.declarations import Function
from slither.analyses.taint.all_variables import is_tainted as is_tainted_from_inputs
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

    WIKI = 'https://github.com/trailofbits/slither/wiki/Vulnerabilities-Description#functions-that-send-ether-to-arbitrary-destinations'

    def arbitrary_send(self, func):
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
                    if isinstance(ir, (HighLevelCall)):
                        if isinstance(ir.function, Function):
                            if ir.function.full_name == 'transferFrom(address,address,uint256)':
                                return False
                    if ir.call_value is None:
                        continue
                    if ir.call_value == SolidityVariableComposed('msg.value'):
                        continue
                    if is_tainted(ir.call_value, SolidityVariableComposed('msg.value')):
                        continue

                    if is_tainted_from_inputs(self.slither, ir.destination):
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

        # Taint msg.value
        taint = SolidityVariableComposed('msg.value')
        run_taint_variable(self.slither, taint)

        # Taint msg.sender
        taint = SolidityVariableComposed('msg.sender')
        run_taint_variable(self.slither, taint)

        for c in self.contracts:
            arbitrary_send = self.detect_arbitrary_send(c)
            for (func, nodes) in arbitrary_send:

                info = "{}.{} ({}) sends eth to arbirary user\n"
                info = info.format(func.contract.name,
                                   func.name,
                                   func.source_mapping_str)
                info += '\tDangerous calls:\n'
                for node in nodes:
                    info += '\t- {} ({})\n'.format(node.expression, node.source_mapping_str)

                self.log(info)

                results.append({'check': self.ARGUMENT,
                                'function':{
                                    'name' : func.name,
                                    'source_mapping': func.source_mapping
                                },
                                'expressions':[{
                                    'expression': str(n.expression),
                                    'source_mapping':n.source_mapping}
                                    for n in nodes]
                                })

        return results
