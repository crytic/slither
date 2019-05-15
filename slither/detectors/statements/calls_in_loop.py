"""
"""
from slither.core.cfg.node import NodeType
from slither.detectors.abstract_detector import (AbstractDetector,
                                                 DetectorClassification)
from slither.slithir.operations import (HighLevelCall, LibraryCall,
                                        LowLevelCall, Send, Transfer)


class MultipleCallsInLoop(AbstractDetector):
    """
    """

    ARGUMENT = 'calls-loop'
    HELP = 'Multiple calls in a loop'
    IMPACT = DetectorClassification.LOW
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = 'https://github.com/crytic/slither/wiki/Detector-Documentation/_edit#calls-inside-a-loop'


    WIKI_TITLE = 'Calls inside a loop'
    WIKI_DESCRIPTION = 'Calls inside a loop might lead to denial of service attack.'
    WIKI_EXPLOIT_SCENARIO = '''
```solidity
contract CallsInLoop{

    address[] destinations;

    constructor(address[] newDestinations) public{
        destinations = newDestinations;
    }

    function bad() external{
        for (uint i=0; i < destinations.length; i++){
            destinations[i].transfer(i);
        }
    }

}
```
If one of the destinations has a fallback function which reverts, `bad` will always revert.'''

    WIKI_RECOMMENDATION = 'Favor [pull over push](https://github.com/ethereum/wiki/wiki/Safety#favor-pull-over-push-for-external-calls) strategy for external calls.'

    @staticmethod
    def call_in_loop(node, in_loop, visited, ret):
        if node in visited:
            return
        # shared visited
        visited.append(node)

        if node.type == NodeType.STARTLOOP:
            in_loop = True
        elif node.type == NodeType.ENDLOOP:
            in_loop = False

        if in_loop:
            for ir in node.irs:
                if isinstance(ir, (LowLevelCall,
                                   HighLevelCall,
                                   Send,
                                   Transfer)):
                    if isinstance(ir, LibraryCall):
                        continue
                    ret.append(node)

        for son in node.sons:
            MultipleCallsInLoop.call_in_loop(son, in_loop, visited, ret)

    @staticmethod
    def detect_call_in_loop(contract):
        ret = []
        for f in contract.functions + contract.modifiers:
            if f.contract_declarer == contract and f.is_implemented:
                MultipleCallsInLoop.call_in_loop(f.entry_point,
                                                 False, [], ret)

        return ret

    def _detect(self):
        """
        """
        results = []
        for c in self.slither.contracts_derived:
            values = self.detect_call_in_loop(c)
            for node in values:
                func = node.function

                info = "{} has external calls inside a loop: \"{}\" ({})\n"
                info = info.format(func.canonical_name, node.expression, node.source_mapping_str)

                json = self.generate_json_result(info)
                self.add_node_to_json(node, json)
                results.append(json)

        return results
