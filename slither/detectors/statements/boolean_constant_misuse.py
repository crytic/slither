"""
Module detecting misuse of Boolean constants
"""
from slither.core.cfg.node import NodeType
from slither.core.solidity_types import ElementaryType
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.slithir.operations import Assignment, Call, Return, InitArray, Binary, BinaryType, Condition
from slither.slithir.variables import Constant


class BooleanConstantMisuse(AbstractDetector):
    """
    Boolean constant misuse
    """

    ARGUMENT = 'boolean-cst'
    HELP = 'Misuse of Boolean constant'
    IMPACT = DetectorClassification.MEDIUM
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = 'https://github.com/crytic/slither/wiki/Detector-Documentation#misuse-of-a-boolean-constant'

    WIKI_TITLE = 'Misuse of a Boolean constant'
    WIKI_DESCRIPTION = '''Detects the misuse of a Boolean constant.'''
    WIKI_EXPLOIT_SCENARIO = '''
```solidity
contract A {
	function f(uint x) public {
		// ...
        if (false) { // bad!
           // ...
        }
		// ...
	}

	function g(bool b) public returns (bool) {
		// ...
        return (b || true); // bad!
		// ...
	}
}
```
Boolean constants in code have only a few legitimate uses. 
Other uses (in complex expressions, as conditionals) indicate either an error or, most likely, the persistence of faulty code.'''

    WIKI_RECOMMENDATION = '''Verify and simplify the condition.'''

    @staticmethod
    def _detect_boolean_constant_misuses(contract):
        """
        Detects and returns all nodes which misuse a Boolean constant.
        :param contract: Contract to detect assignment within.
        :return: A list of misusing nodes.
        """

        # Create our result set.
        results = []

        # Loop for each function and modifier.
        for function in contract.functions_declared:
            f_results = set()

            # Loop for every node in this function, looking for boolean constants
            for node in function.nodes:

                # Do not report "while(true)"
                if node.type == NodeType.IFLOOP:
                    if node.irs:
                        if len(node.irs) == 1:
                            ir = node.irs[0]
                            if isinstance(ir, Condition) and ir.value == Constant('True', ElementaryType('bool')):
                                continue

                for ir in node.irs:
                    if isinstance(ir, (Assignment, Call, Return, InitArray)):
                        # It's ok to use a bare boolean constant in these contexts
                        continue
                    if isinstance(ir, Binary):
                        if ir.type in [BinaryType.ADDITION, BinaryType.EQUAL, BinaryType.NOT_EQUAL]:
                            # Comparing to a Boolean constant is dubious style, but harmless
                            # Equal is catch by another detector (informational severity)
                            continue
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
            boolean_constant_misuses = self._detect_boolean_constant_misuses(contract)
            if boolean_constant_misuses:
                for (func, nodes) in boolean_constant_misuses:
                    for node in nodes:
                        info = [func, " uses a Boolean constant improperly:\n\t-", node, "\n"]

                        res = self.generate_result(info)
                        results.append(res)
                
        return results
