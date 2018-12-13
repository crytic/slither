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
from slither.slithir.operations import Binary, BinaryType


class Timestamp(AbstractDetector):
    """
    """

    ARGUMENT = 'timestamp'
    HELP = 'Dangerous usage of `block.timestamp`'
    IMPACT = DetectorClassification.LOW
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = 'https://github.com/trailofbits/slither/wiki/Vulnerabilities-Description#block-timestamp'

    def timestamp(self, func):
        """
        """

        ret = set()
        for node in func.nodes:
            if node.contains_require_or_assert():
                for var in node.variables_read:
                    if is_tainted(var, SolidityVariableComposed('block.timestamp')):
                        ret.add(node)
            for ir in node.irs:
                if isinstance(ir, Binary) and BinaryType.return_bool(ir.type):
                    for var in ir.read:
                        if is_tainted(var, SolidityVariableComposed('block.timestamp')):
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
        for f in [f for f in contract.functions if f.contract == contract]:
            nodes = self.timestamp(f)
            if nodes:
                ret.append((f, nodes))
        return ret

    def detect(self):
        """
        """
        results = []

        # Taint block.timestamp
        taint = SolidityVariableComposed('block.timestamp')
        run_taint_variable(self.slither, taint)

        for c in self.contracts:
            dangerous_timestamp = self.detect_dangerous_timestamp(c)
            for (func, nodes) in dangerous_timestamp:

                info = "{}.{} ({}) uses timestamp for comparisons\n"
                info = info.format(func.contract.name,
                                   func.name,
                                   func.source_mapping_str)
                info += '\tDangerous comparisons:\n'
                for node in nodes:
                    info += '\t- {} ({})\n'.format(node.expression, node.source_mapping_str)

                self.log(info)


                json = self.generate_json_result(info)
                self.add_function_to_json(func, json)
                self.add_nodes_to_json(nodes, json)
                results.append(json)

        return results
