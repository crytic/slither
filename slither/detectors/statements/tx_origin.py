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

    @staticmethod
    def _contains_incorrect_tx_origin_use(node):
        """
             Check if the node read tx.origin and dont read msg.sender
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

    def detect(self):
        """ Detect the functions that use tx.origin in a conditional node
        """
        results = []
        for c in self.contracts:
            values = self.detect_tx_origin(c)
            for func, nodes in values:
                func_name = func.name
                info = "tx.origin in %s, Contract: %s, Function: %s" % (self.filename,
                                                                        c.name,
                                                                        func_name)
                self.log(info)

                sourceMapping = [n.source_mapping for n in nodes]

                results.append({'vuln': 'TxOrigin',
                                'sourceMapping': sourceMapping,
                                'filename': self.filename,
                                'contract': c.name,
                                'function_name': func_name})

        return results
