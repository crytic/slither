"""
Module detecting numbers with too many digits.
"""

import re
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.slithir.variables import Constant

_HEX_ADDRESS_REGEXP = re.compile("(0x)?[0-9a-f]{40}", re.IGNORECASE | re.ASCII)


def is_hex_address(value) -> bool:
    """
    Checks if the given string of text type is an address in hexadecimal encoded form.
    """
    return _HEX_ADDRESS_REGEXP.fullmatch(value) is not None


class TooManyDigits(AbstractDetector):
    """
    Detect numbers with too many digits
    """

    ARGUMENT = "too-many-digits"
    HELP = "Conformance to numeric notation best practices"
    IMPACT = DetectorClassification.INFORMATIONAL
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#too-many-digits"
    WIKI_TITLE = "Too many digits"

    # region wiki_description
    WIKI_DESCRIPTION = """
Literals with many digits are difficult to read and review.
"""
    # endregion wiki_description

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """
```solidity
contract MyContract{
    uint 1_ether = 10000000000000000000; 
}
```

While `1_ether` looks like `1 ether`, it is `10 ether`. As a result, it's likely to be used incorrectly.
"""
    # endregion wiki_exploit_scenario

    # region wiki_recommendation
    WIKI_RECOMMENDATION = """
Use:
- [Ether suffix](https://solidity.readthedocs.io/en/latest/units-and-global-variables.html#ether-units),
- [Time suffix](https://solidity.readthedocs.io/en/latest/units-and-global-variables.html#time-units), or
- [The scientific notation](https://solidity.readthedocs.io/en/latest/types.html#rational-and-integer-literals)
"""
    # endregion wiki_recommendation

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
                        if "00000" in value_as_str and not is_hex_address(value_as_str):
                            # Info to be printed
                            ret.append(node)
        return ret

    def _detect(self):
        results = []

        # iterate over all contracts
        for contract in self.compilation_unit.contracts_derived:
            # iterate over all functions
            for f in contract.functions:
                # iterate over all the nodes
                ret = self._detect_too_many_digits(f)
                if ret:
                    func_info = [f, " uses literals with too many digits:"]
                    for node in ret:
                        node_info = func_info + ["\n\t- ", node, "\n"]

                        # Add the result in result
                        res = self.generate_result(node_info)
                        results.append(res)

        return results
