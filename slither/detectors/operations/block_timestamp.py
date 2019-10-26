"""
    Module detecting dangerous use of block.timestamp

"""
from slither.core.declarations import Function
from slither.analyses.data_dependency.data_dependency import is_tainted, is_dependent
from slither.core.declarations.solidity_variables import (SolidityFunction,
                                                          SolidityVariableComposed)
from slither.detectors.abstract_detector import (AbstractDetector,
                                                 DetectorClassification)
from slither.slithir.operations import Binary, BinaryType
from slither.utils import json_utils


class Timestamp(AbstractDetector):
    """
    """

    ARGUMENT = 'timestamp'
    HELP = 'Dangerous usage of `block.timestamp`'
    IMPACT = DetectorClassification.LOW
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = 'https://github.com/crytic/slither/wiki/Detector-Documentation#block-timestamp'


    WIKI_TITLE = 'Block timestamp'
    WIKI_DESCRIPTION = 'Dangerous usage of `block.timestamp`. `block.timestamp` can be manipulated by miners.'
    WIKI_EXPLOIT_SCENARIO = '''"Bob's contract relies on `block.timestamp` for its randomness. Eve is a miner and manipulates `block.timestamp` to exploit Bob's contract.'''
    WIKI_RECOMMENDATION = 'Avoid relying on `block.timestamp`.'

    def timestamp(self, func):
        """
        """

        ret = set()
        for node in func.nodes:
            if node.contains_require_or_assert():
                for var in node.variables_read:
                    if is_dependent(var, SolidityVariableComposed('block.timestamp'), func.contract):
                        ret.add(node)
            for ir in node.irs:
                if isinstance(ir, Binary) and BinaryType.return_bool(ir.type):
                    for var in ir.read:
                        if is_dependent(var, SolidityVariableComposed('block.timestamp'), func.contract):
                            ret.add(node)
        return list(ret)


    def detect_dangerous_timestamp(self, contract):
        """
        Args:
            contract (Contract)
        Returns:
            list((Function), (list (Node)))
        """
        ret = []
        for f in [f for f in contract.functions if f.contract_declarer == contract]:
            nodes = self.timestamp(f)
            if nodes:
                ret.append((f, nodes))
        return ret

    def _detect(self):
        """
        """
        results = []

        for c in self.contracts:
            dangerous_timestamp = self.detect_dangerous_timestamp(c)
            for (func, nodes) in dangerous_timestamp:

                info = "{} ({}) uses timestamp for comparisons\n"
                info = info.format(func.canonical_name,
                                   func.source_mapping_str)
                info += '\tDangerous comparisons:\n'
                for node in nodes:
                    info += '\t- {} ({})\n'.format(node.expression, node.source_mapping_str)

                json = self.generate_json_result(info)
                json_utils.add_function_to_json(func, json)
                json_utils.add_nodes_to_json(nodes, json)
                results.append(json)

        return results
