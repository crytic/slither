"""
Module detecting comparison of uint greater than zero
"""
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.slithir.operations import (
    Binary,
    BinaryType,
)

class ComparingUintGTZero(AbstractDetector):
    """
    Documentation
    """

    ARGUMENT = 'comparing-uint-gt-zero'
    HELP = 'Comparing uint types greater than zero'
    IMPACT = DetectorClassification.OPTIMIZATION
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = 'https://github.com/crytic/slither/wiki/Detector-Documentation#comparing-uint-gt-zero'

    WIKI_TITLE = 'Comparing uint greater than zero'
    WIKI_DESCRIPTION = 'uints are either 0 or greater. Comparing it different than 0 has the same effect but uses less gas.'
    WIKI_EXPLOIT_SCENARIO = 'Avoid comparing uint greater than 0. Instead check if it\'s different than 0.'
    WIKI_RECOMMENDATION = 'Avoid comparing uint greater than 0.'

    @staticmethod
    def detect_uint_compared_gt_zero(contract):
        """
        Detects and returns all nodes which compare a uint greater than 0
        :param contract: Contract to detect assignment within.
        :return: A list of nodes with unnecessary comparisons. 
        """

        # Create our result set
        results = []

        # Loop for each function and modifier
        for function in contract.functions_declared:
            nodes = set()
            variables = set()
            # Loop for every node in this function
            for node in function.nodes:
                # Loop for each operation, looking for a uint > 0 comparison
                for ir in node.irs:
                    if isinstance(ir, Binary):
                        if (ir.type == BinaryType.GREATER 
                            and ir.variable_left.type.min == 0
                            and ir.variable_right == 0
                        ):
                            nodes.add(node)
                            variables.add(ir.variable_left)
                        if (ir.type == BinaryType.LESS
                            and ir.variable_left == 0
                            and ir.variable_right.type.min == 0
                        ):
                            nodes.add(node)
                            variables.add(ir.variable_right)
            results.append((function, nodes, variables))

        # Return the resulting set of node with unnecessary comparisons of uint greater than zero
        return results

    def _detect(self):
        results = []

        for contract in self.contracts:
            uint_dt_zero_compararisons = self.detect_uint_compared_gt_zero(contract)
            for (func, nodes, variables) in uint_dt_zero_compararisons:
                for node in nodes:
                    for v in variables:
                        info = [
                            func,
                            " compares " + v.name + " of type " + v.type.name + " greater than zero:\n\t-> ",
                            node,
                            "\n",
                        ]

                        res = self.generate_result(info)
                        results.append(res)

        return results