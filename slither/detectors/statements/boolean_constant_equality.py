"""
Module detecting misuse of Boolean constants
"""

from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.slithir.operations import Assignment, Call, Return, InitArray, Binary, BinaryType
from slither.slithir.variables import Constant


class BooleanEquality(AbstractDetector):
    """
    Boolean constant misuse
    """

    ARGUMENT = 'boolean-equal'
    HELP = 'Comparison to boolean constant'
    IMPACT = DetectorClassification.INFORMATIONAL
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = 'https://github.com/trailofbits/slither-private/wiki/Vulnerabilities-Description#boolean-equality'

    WIKI_TITLE = 'Boolean Equality'
    WIKI_DESCRIPTION = '''Detects the comparison to boolean constant.'''
    WIKI_EXPLOIT_SCENARIO = '''
```solidity
contract A {
	function f(bool x) public {
		// ...
        if (x == true) { // bad!
           // ...
        }
		// ...
	}
}
```
Boolean can be used directly and do not need to be compare to `true` or `false`.'''

    WIKI_RECOMMENDATION = '''Remove the equality to the boolean constant.'''

    @staticmethod
    def _detect_boolean_equality(contract):

        # Create our result set.
        results = []

        # Loop for each function and modifier.
        for function in contract.functions_and_modifiers_declared:
            f_results = set()

            # Loop for every node in this function, looking for boolean constants
            for node in function.nodes:
                for ir in node.irs:
                    if isinstance(ir, Binary):
                        if ir.type in [BinaryType.EQUAL, BinaryType.NOT_EQUAL]:
                            for r in ir.read:
                                if isinstance(r, Constant):
                                    if type(r.value) is bool:
                                        f_results.add(node)
                results.append((function, f_results))

        # Return the resulting set of nodes with improper uses of Boolean constants
        return results

    def _detect(self):
        """
        Detect Boolean constant misuses
        """
        results = []
        for contract in self.contracts:
            boolean_constant_misuses = self._detect_boolean_equality(contract)
            if boolean_constant_misuses:
                for (func, nodes) in boolean_constant_misuses:
                    for node in nodes:
                        info = [func, " compares to a boolean constant:\n\t-", node, "\n"]

                        res = self.generate_result(info)
                        results.append(res)

        return results
