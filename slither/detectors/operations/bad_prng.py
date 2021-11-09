"""
Module detecting bad PRNG due to the use of block.timestamp, now or blockhash (block.blockhash) as a source of randomness
"""

from slither.slithir.operations.lvalue import OperationWithLValue
from slither.slithir.variables.constant import Constant
from slither.analyses.data_dependency.data_dependency import is_dependent
from slither.core.declarations.solidity_variables import (
    SolidityVariable,
    SolidityFunction,
    SolidityVariableComposed,
)
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.slithir.operations import BinaryType, Binary,Return
from slither.slithir.operations import SolidityCall


block_variables = {
    SolidityVariableComposed("block.timestamp"),
    SolidityVariable("now"),
    SolidityVariableComposed("block.coinbase"),
    SolidityVariableComposed("block.difficulty"),
    SolidityVariableComposed("block.gaslimit"),
    SolidityVariableComposed("block.number")
}
hash_functions = {
    SolidityFunction("keccak256()"),
    SolidityFunction("keccak256(bytes)"),
    SolidityFunction("sha256()"),
    SolidityFunction("sha256(bytes)"),
    SolidityFunction("sha3()")
}
blockhash_functions = {
    SolidityFunction("blockhash(uint256)"),
    SolidityVariableComposed("block.blockhash"),
}

def collect_Constructor_values(functions):
    """
        Return the constructor variables and constant
    Args:
        f (Function)
    Returns:
        list(values)
    """
    nodes = []
    all_constructor_values = {}
    only_block_constructor_values = {}

    for f in functions:
        if f.name == "slitherConstructorVariables":
            nodes += f.nodes
        if f.name == "slitherConstructorConstantVariables":
            nodes += f.nodes
        
    nodes.sort(key=lambda x: x.source_mapping['lines'])

    for n in nodes:
        if len(n.irs) == 0:
            continue
        if not n.irs[-1].lvalue:
            continue

        lvalue = n.irs[-1].lvalue
        if lvalue.visibility in ["public", "external"]:
            continue
        all_constructor_values[lvalue] = []
        for var in n.variables_read:
            if (var in block_variables) or (var in only_block_constructor_values):
                only_block_constructor_values[lvalue] = False
                break

    return (all_constructor_values, only_block_constructor_values)


def check_constructor_variables(func, only_block_constructor_values):
    ret = []

    for node in func.nodes:
        if len(node.irs) == 0:
            continue
        lvalue = node.irs[-1].lvalue
        if (lvalue in only_block_constructor_values
            and only_block_constructor_values[lvalue] == True
        ):
            ret.append(node)

    return ret


def contains_bad_PRNG_sources(func, all_constructor_values, only_block_constructor_values):
    """
         Check if any node in function has a modulus operator and the first operand is dependent on block.timestamp, now or blockhash()
    Returns:
        (nodes)
    """
    ret = []
    mod_in_ret = {}
    weak_prng_tainted = {}
    block_tmps = all_constructor_values

    # pylint: disable=too-many-nested-blocks
    for node in func.nodes:
        for ir in node.irs:
            if (
                isinstance(ir, SolidityCall)
                and ir.function in blockhash_functions
            ):
                weak_prng_tainted[ir.lvalue] = []
                if node not in ret:
                    ret.append(node)
                
                var = ir.arguments[0]
                if isinstance(var, Constant):
                    continue

                if var in only_block_constructor_values:
                    block_tmps[var] += [node]

                if var in weak_prng_tainted:
                    for n in weak_prng_tainted[var]:
                        if n not in ret:
                            ret.append(n)

            elif isinstance(ir, Binary) and ir.type == BinaryType.MODULO:
                var = ir.read[0]
                if (
                    var in block_variables
                    or var in only_block_constructor_values
                    or var in weak_prng_tainted
                ):
                    weak_prng_tainted[ir.lvalue] = [node]
                    last_ir = node.irs[-1]
                    if (
                        isinstance(last_ir, OperationWithLValue)
                        and is_dependent(last_ir.lvalue, var, func.contract)
                    ):
                        for lvalue in mod_in_ret:
                            if weak_prng_tainted[lvalue][0] in weak_prng_tainted[var]:
                                mod_in_ret[lvalue] = False
                        continue
                    
                    mod_in_ret[ir.lvalue] = True
                    
                    if var in only_block_constructor_values:
                        block_tmps[var] += [node]
                    
                    if var in weak_prng_tainted:
                        weak_prng_tainted[ir.lvalue] += weak_prng_tainted[var]

                        for lvalue in mod_in_ret:
                            if weak_prng_tainted[lvalue][0] in weak_prng_tainted[var]:
                                mod_in_ret[lvalue] = True

            elif (
                isinstance(ir, SolidityCall)
                and ir.function in hash_functions
            ):
                is_weak_value = 0
                for var in ir.read:
                    if isinstance(var, Constant):
                        continue

                    if (
                        var in block_variables
                        or var in all_constructor_values
                        or var in weak_prng_tainted
                    ):
                        if is_weak_value == 0:
                            weak_prng_tainted[ir.lvalue] = [node]
                            is_weak_value += 1

                        if var in only_block_constructor_values:
                            block_tmps[var] += [node]

                        if var in weak_prng_tainted:
                            weak_prng_tainted[ir.lvalue] += weak_prng_tainted[var]
                    
            elif isinstance(ir, OperationWithLValue):
                for var in ir.read:
                    if isinstance(var, Constant):
                        continue
                    
                    if (
                        var in block_variables
                        or var in all_constructor_values
                        or var in weak_prng_tainted
                    ):
                        weak_prng_tainted[ir.lvalue] = [node]

                        if var in only_block_constructor_values:
                            block_tmps[var] += [node] 

                        if var in weak_prng_tainted:
                            weak_prng_tainted[ir.lvalue] += weak_prng_tainted[var]

                            if  isinstance(ir, Binary) and ir.type != BinaryType.ADDITION:
                                (l,r) = ir.read
                                check = None
                                if l == var:
                                    check = r
                                else:
                                    check = l
                                if isinstance(check, Constant) or check in all_constructor_values or check in func.parameters:
                                    continue
                                for lvalue in mod_in_ret:
                                    if weak_prng_tainted[lvalue][0] in weak_prng_tainted[var]:
                                        mod_in_ret[lvalue] = False

    for lvalue in mod_in_ret:
        if mod_in_ret[lvalue] == True:
            for n in weak_prng_tainted[lvalue]:
                if n not in ret:
                    ret.append(n)

    for key in block_tmps:
        if len(block_tmps[key]) > 0:
            for n in block_tmps[key]:
                if n in ret:
                    only_block_constructor_values[key] = True
                break

    return ret


def detect_bad_PRNG(contract):
    """
    Args:
        contract (Contract)
    Returns:
        list((Function), (list (Node)))
    """
    if len(contract.functions)>1:
        (all_constructor_values, only_block_constructor_values) = collect_Constructor_values(contract.functions[-2 : ])
    elif len(contract.functions)>0:
        (all_constructor_values, only_block_constructor_values) = collect_Constructor_values(contract.functions[-1 : ])
    
    ret = []
    for f in contract.functions:
        if f.name == "slitherConstructorVariables" or f.name == "slitherConstructorConstantVariables":
            bad_prng_nodes = check_constructor_variables(f, only_block_constructor_values)
        else:
            bad_prng_nodes = contains_bad_PRNG_sources(f, all_constructor_values, only_block_constructor_values)

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
                info = [func, " uses a weak PRNG\n"]
                nodes.sort(key=lambda x: x.node_id)
                for node in nodes:
                    info += ["\t- ", node, "\n"]
                    
                res = self.generate_result(info)
                results.append(res)

        return results