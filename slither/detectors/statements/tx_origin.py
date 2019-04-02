"""
Module detecting usage of `tx.origin` in a conditional node
"""

from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification

class TxOrigin(AbstractDetector):
    """
    Detect usage of tx.origin in a conditional node
    """

    ARGUMENT = 'tx-origin'
    HELP = 'Dangerous usage of `tx.origin`'
    IMPACT = DetectorClassification.MEDIUM
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = 'https://github.com/crytic/slither/wiki/Detector-Documentation#dangerous-usage-of-txorigin'

    WIKI_TITLE = 'Dangerous usage of `tx.origin`'
    WIKI_DESCRIPTION = '`tx.origin`-based protection can be abused by malicious contract if a legitimate user interacts with the malicious contract.'
    WIKI_EXPLOIT_SCENARIO = '''
```solidity
contract TxOrigin {
    address owner = msg.sender;

    function bug() {
        require(tx.origin == owner);
    }
```
Bob is the owner of `TxOrigin`. Bob calls Eve's contract. Eve's contract calls `TxOrigin` and bypasses the `tx.origin` protection.'''

    WIKI_RECOMMENDATION = 'Do not use `tx.origin` for authorization.'

    @staticmethod
    def _contains_incorrect_tx_origin_use(node):
        """
             Check if the node reads tx.origin and doesn't read msg.sender
             Avoid the FP due to (msg.sender == tx.origin)
        Returns:
            (bool)
        """
        solidity_var_read = node.solidity_variables_read
        if solidity_var_read:
            return any(v.name == 'tx.origin' for v in solidity_var_read) and\
                   all(v.name != 'msg.sender' for v in solidity_var_read)
        return False

    def detect_tx_origin(self, contract):
        ret = []
        for f in contract.functions:

            nodes = f.nodes
            condtional_nodes = [n for n in nodes if n.contains_if() or
                                n.contains_require_or_assert()]
            bad_tx_nodes = [n for n in condtional_nodes if
                            self._contains_incorrect_tx_origin_use(n)]
            if bad_tx_nodes:
                ret.append((f, bad_tx_nodes))
        return ret

    def _detect(self):
        """ Detect the functions that use tx.origin in a conditional node
        """
        results = []
        for c in self.contracts:
            values = self.detect_tx_origin(c)
            for func, nodes in values:
                info = "{}.{} uses tx.origin for authorization:\n"
                info = info.format(func.contract.name, func.name)

                for node in nodes:
                    info += "\t- {} ({})\n".format(node.expression, node.source_mapping_str)

                json = self.generate_json_result(info)
                self.add_function_to_json(func, json)
                self.add_nodes_to_json(nodes, json)
                results.append(json)

        return results
