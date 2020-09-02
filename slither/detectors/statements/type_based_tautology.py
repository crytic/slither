"""
Module detecting tautologies and contradictions based on types in comparison operations over integers
"""

from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.slithir.operations import Binary, BinaryType
from slither.slithir.variables import Constant
from slither.core.solidity_types.elementary_type import Int, Uint


def typeRange(t):
    bits = int(t.split("int")[1])
    if t in Uint:
        return 0, (2 ** bits) - 1
    if t in Int:
        v = (2 ** (bits - 1)) - 1
        return -v, v
    return None


def _detect_tautology_or_contradiction(low, high, cval, op):
    """
    Return true if "[low high] op cval " is always true or always false
    :param low:
    :param high:
    :param cval:
    :param op:
    :return:
    """
    if op == BinaryType.LESS:
        # a < cval
        # its a tautology if
        # high(a) < cval
        # its a contradiction if
        # low(a) >= cval
        return high < cval or low >= cval
    if op == BinaryType.GREATER:
        # a > cval
        # its a tautology if
        # low(a) > cval
        # its a contradiction if
        # high(a) <= cval
        return low > cval or high <= cval
    if op == BinaryType.LESS_EQUAL:
        # a <= cval
        # its a tautology if
        # high(a) <= cval
        # its a contradiction if
        # low(a) > cval
        return (high <= cval) or (low > cval)
    if op == BinaryType.GREATER_EQUAL:
        # a >= cval
        # its a tautology if
        # low(a) >= cval
        # its a contradiction if
        # high(a) < cval
        return (low >= cval) or (high < cval)
    return False


class TypeBasedTautology(AbstractDetector):
    """
    Type-based tautology or contradiction
    """

    ARGUMENT = "tautology"
    HELP = "Tautology or contradiction"
    IMPACT = DetectorClassification.MEDIUM
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#tautology-or-contradiction"

    WIKI_TITLE = "Tautology or contradiction"
    WIKI_DESCRIPTION = """Detects expressions that are tautologies or contradictions."""
    WIKI_EXPLOIT_SCENARIO = """
```solidity
contract A {
	function f(uint x) public {
		// ...
        if (x >= 0) { // bad -- always true
           // ...
        }
		// ...
	}

	function g(uint8 y) public returns (bool) {
		// ...
        return (y < 512); // bad!
		// ...
	}
}
```
`x` is a `uint256`, so `x >= 0` will be always true.
`y` is a `uint8`, so `y <512` will be always true.  
"""

    WIKI_RECOMMENDATION = (
        """Fix the incorrect comparison by changing the value type or the comparison."""
    )

    flip_table = {
        BinaryType.GREATER: BinaryType.LESS,
        BinaryType.GREATER_EQUAL: BinaryType.LESS_EQUAL,
        BinaryType.LESS: BinaryType.GREATER,
        BinaryType.LESS_EQUAL: BinaryType.GREATER_EQUAL,
    }

    def detect_type_based_tautologies(self, contract):
        """
        Detects and returns all nodes with tautology/contradiction comparisons (based on type alone).
        :param contract: Contract to detect assignment within.
        :return: A list of nodes with tautolgies/contradictions.
        """

        # Create our result set.
        results = []
        allInts = Int + Uint

        # Loop for each function and modifier.
        for function in contract.functions_declared:  # pylint: disable=too-many-nested-blocks
            f_results = set()

            for node in function.nodes:
                for ir in node.irs:
                    if isinstance(ir, Binary) and ir.type in self.flip_table:
                        # If neither side is a constant, we can't do much
                        if isinstance(ir.variable_left, Constant):
                            cval = ir.variable_left.value
                            rtype = str(ir.variable_right.type)
                            if rtype in allInts:
                                (low, high) = typeRange(rtype)
                                if _detect_tautology_or_contradiction(
                                    low, high, cval, self.flip_table[ir.type]
                                ):
                                    f_results.add(node)

                        if isinstance(ir.variable_right, Constant):
                            cval = ir.variable_right.value
                            ltype = str(ir.variable_left.type)
                            if ltype in allInts:
                                (low, high) = typeRange(ltype)
                                if _detect_tautology_or_contradiction(
                                    low, high, cval, ir.type
                                ):
                                    f_results.add(node)
            results.append((function, f_results))

        # Return the resulting set of nodes with tautologies and contradictions
        return results

    def _detect(self):
        """
        Detect tautological (or contradictory) comparisons
        """
        results = []
        for contract in self.contracts:
            tautologies = self.detect_type_based_tautologies(contract)
            if tautologies:
                for (func, nodes) in tautologies:
                    for node in nodes:
                        info = [func, " contains a tautology or contradiction:\n"]
                        info += ["\t- ", node, "\n"]

                        res = self.generate_result(info)
                        results.append(res)

        return results
