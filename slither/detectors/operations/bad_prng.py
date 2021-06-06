"""
Module detecting bad PRNG due to the use of block.timestamp, now or blockhash (block.blockhash) as a source of randomness
"""

from slither.analyses.data_dependency.data_dependency import is_dependent_ssa
from slither.core.declarations.solidity_variables import (
    SolidityVariable,
    SolidityFunction,
    SolidityVariableComposed,
)
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.slithir.operations import BinaryType, Binary
from slither.slithir.operations import SolidityCall


def collect_return_values_of_bad_PRNG_functions(f):
    """
        Return the return-values of calls to blockhash()
    Args:
        f (Function)
    Returns:
        list(values)
    """
    values_returned = []
    for n in f.nodes:
        for ir in n.irs_ssa:
            if (
                isinstance(ir, SolidityCall)
                and ir.function == SolidityFunction("blockhash(uint256)")
                and ir.lvalue
            ):
                values_returned.append(ir.lvalue)
    return values_returned


def contains_bad_PRNG_sources(func, blockhash_ret_values):
    """
         Check if any node in function has a modulus operator and the first operand is dependent on block.timestamp, now or blockhash()
    Returns:
        (nodes)
    """
    ret = set()
    # pylint: disable=too-many-nested-blocks
    for node in func.nodes:
        for ir in node.irs_ssa:
            if isinstance(ir, Binary) and ir.type == BinaryType.MODULO:
                if is_dependent_ssa(
                    ir.variable_left, SolidityVariableComposed("block.timestamp"), func.contract
                ) or is_dependent_ssa(ir.variable_left, SolidityVariable("now"), func.contract):
                    ret.add(node)
                    break

                for ret_val in blockhash_ret_values:
                    if is_dependent_ssa(ir.variable_left, ret_val, func.contract):
                        ret.add(node)
                        break
    return list(ret)


def detect_bad_PRNG(contract):
    """
    Args:
        contract (Contract)
    Returns:
        list((Function), (list (Node)))
    """
    blockhash_ret_values = []
    for f in contract.functions:
        blockhash_ret_values += collect_return_values_of_bad_PRNG_functions(f)
    ret = []
    for f in contract.functions:
        bad_prng_nodes = contains_bad_PRNG_sources(f, blockhash_ret_values)
        if bad_prng_nodes:
            ret.append((f, bad_prng_nodes))
    return ret


class BadPRNG(AbstractDetector):
    """
    Detect weak PRNG due to a modulo operation on block.timestamp, now or blockhash
    """

    ARGUMENT = "weak-prng"
    HELP = "Weak PRNG"
    IMPACT = DetectorClassification.HIGH
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#weak-PRNG"

    WIKI_TITLE = "Weak PRNG"
    WIKI_DESCRIPTION = "Weak PRNG due to a modulo on `block.timestamp`, `now` or `blockhash`. These can be influenced by miners to some extent so they should be avoided."

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """
```solidity
contract Game {

    uint reward_determining_number;

    function guessing() external{
      reward_determining_number = uint256(block.blockhash(10000)) % 10;
    }
}
```
Eve is a miner. Eve calls `guessing` and re-orders the block containing the transaction. 
As a result, Eve wins the game."""
    # endregion wiki_exploit_scenario

    WIKI_RECOMMENDATION = (
        "Do not use `block.timestamp`, `now` or `blockhash` as a source of randomness"
    )

    def _detect(self):
        """Detect bad PRNG due to the use of block.timestamp, now or blockhash (block.blockhash) as a source of randomness"""
        results = []
        for c in self.compilation_unit.contracts_derived:
            values = detect_bad_PRNG(c)
            for func, nodes in values:

                for node in nodes:
                    info = [func, ' uses a weak PRNG: "', node, '" \n']
                    res = self.generate_result(info)
                    results.append(res)

        return results
