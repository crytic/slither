"""
Module detecting numbers with too many digits.
"""

from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.slithir.variables import Constant
from slither.utils import json_utils


class TooManyDigits(AbstractDetector):
    """
    Detect numbers with too many digits
    """

    ARGUMENT = 'too-many-digits'
    HELP = 'Conformance to numeric notation best practices'
    IMPACT = DetectorClassification.INFORMATIONAL
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = 'https://github.com/crytic/slither/wiki/Detector-Documentation#too-many-digits'
    WIKI_TITLE = 'Too many digits'
    WIKI_DESCRIPTION = '''
Literals with many digits are difficult to read and review.
'''
    WIKI_EXPLOIT_SCENARIO = '''
```solidity
contract MyContract{
    uint 1_ether = 10000000000000000000; 
}
```

While `1_ether` looks like `1 ether`, it is `10 ether`. As a result, its usage is likely to be incorrect.
'''
    WIKI_RECOMMENDATION = '''
Use:
- [Ether suffix](https://solidity.readthedocs.io/en/latest/units-and-global-variables.html#ether-units)
- [Time suffix](https://solidity.readthedocs.io/en/latest/units-and-global-variables.html#time-units), or
- [The scientific notation](https://solidity.readthedocs.io/en/latest/types.html#rational-and-integer-literals)
'''

    @staticmethod
    def _detect_too_many_digits(f):
        ret = []
        for node in f.nodes:
            # each node contains a list of IR instruction
            for ir in node.irs:
                # iterate over all the variables read by the IR
                for read in ir.read:
                    # if the variable is a constant
                    if isinstance(read, Constant):
                        # read.value can return an int or a str. Convert it to str
                        value_as_str = read.original_value
                        if '00000' in value_as_str:
                            # Info to be printed
                            ret.append(node)
        return ret

    def _detect(self):
        results = []

        # iterate over all contracts
        for contract in self.slither.contracts_derived:
        # iterate over all functions
            for f in contract.functions:
                # iterate over all the nodes
                ret = self._detect_too_many_digits(f)
                if ret:
                    func_info = '{}.{} ({}) uses literals with too many digits:'.format(f.contract.name,
                                                                                   f.name,
                                                                                   f.source_mapping_str)
                    for node in ret:
                        node_info = func_info + '\n\t- {}\n'.format(node.expression)

                        # Add the result in result
                        json = self.generate_json_result(node_info)
                        json_utils.add_node_to_json(node, json)
                        results.append(json)

        return results
