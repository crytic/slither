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
from slither.analyses.data_dependency.data_dependency import is_tainted, is_dependent
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

    WIKI = 'https://github.com/crytic/slither/wiki/Detector-Documentation#functions-that-send-ether-to-arbitrary-destinations'

    WIKI_TITLE = 'Functions that send ether to arbitrary destinations'
    WIKI_DESCRIPTION = 'Unprotected call to a function executing sending ethers to an arbitrary address.'
    WIKI_EXPLOIT_SCENARIO = '''
```solidity
contract ArbitrarySend{
    address destination;
    function setDestination(){
        destination = msg.sender;
    }

    function withdraw() public{
        destination.transfer(this.balance);
    }
}
```
Bob calls `setDestination` and `withdraw`. As a result he withdraws the contract's balance.'''

    WIKI_RECOMMENDATION = 'Ensure that an arbitrary user cannot withdraw unauthorize funds.'

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
                    if is_dependent(ir.variable_right, SolidityVariableComposed('msg.sender'), func.contract):
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
                    if is_dependent(ir.call_value, SolidityVariableComposed('msg.value'), func.contract):
                        continue

                    if is_tainted(ir.destination, func.contract):
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

    def _detect(self):
        """
        """
        results = []

        for c in self.contracts:
            arbitrary_send = self.detect_arbitrary_send(c)
            for (func, nodes) in arbitrary_send:

                info = "{}.{} ({}) sends eth to arbitrary user\n"
                info = info.format(func.contract.name,
                                   func.name,
                                   func.source_mapping_str)
                info += '\tDangerous calls:\n'
                for node in nodes:
                    info += '\t- {} ({})\n'.format(node.expression, node.source_mapping_str)

                json = self.generate_json_result(info)
                self.add_function_to_json(func, json)
                self.add_nodes_to_json(nodes, json)
                results.append(json)

        return results
