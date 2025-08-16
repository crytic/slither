from typing import List, Dict, Tuple
from slither.core.declarations.contract import Contract
from slither.core.cfg.node import Node
from slither.core.declarations.function import Function
from slither.slithir.operations.operation import Operation
from slither.slithir.operations import TypeConversion
from slither.core.expressions.literal import Literal
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.slithir.operations import SolidityCall
from slither.core.declarations.solidity_variables import SolidityFunction
from slither.slithir.operations.assignment import Assignment
from slither.slithir.variables.reference import ReferenceVariable
from slither.slithir.variables.constant import Constant
from slither.utils.function import get_function_id
from slither.utils.output import Output


def get_signatures(c: Contract) -> Dict[str, str]:
    """Build a dictionary mapping function ids to signature, name, arguments for a contract"""
    result = {}
    functions = c.functions
    for f in functions:
        if f.visibility not in ["public", "external"]:
            continue
        if f.is_constructor or f.is_fallback:
            continue
        result[get_function_id(f.full_name)] = (f.full_name, *f.signature[:2])

    variables = c.state_variables
    for variable in variables:
        if variable.visibility not in ["public"]:
            continue
        name = variable.full_name
        result[get_function_id(name)] = (name, (), ())

    return result


class WrongEncodeWithSelector(AbstractDetector):
    """
    Detect calls to abi.encodeWithSelector that may result in unexpected calldata encodings
    """

    ARGUMENT = "wrong-encode-selector"
    HELP = "abi.encodeWithSelector with unexpected arguments"
    IMPACT = DetectorClassification.MEDIUM
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = "https://github.com/trailofbits/slither/wiki/encode-with-selector"
    WIKI_TITLE = "Parameters of incorrect type or number in abi.encodeWithSelector"
    WIKI_DESCRIPTION = "Wrong number or type of arguments in abi.encodeWithSelector"
    WIKI_EXPLOIT_SCENARIO = """
```solidity
contract Test {   
    event Val(uint, uint);
    function f(uint a, uint b) public {
        emit Val(a, b);
    }
}
contract D {
    function g() public {
        Test t = new Test();
        address(t).call(abi.encodeWithSelector(Test.f.selector, "test"));
    }
}
```
abi.encodeWithSelector's arguments do not match the types expected in the function signature.
function signature.
"""
    WIKI_RECOMMENDATION = "Make sure that the type and number of arguments passed to abi.encodeWithSelector are the same as the target function signature."

    def _detect(self) -> List[Output]:
        # gather all known funcids
        func_ids = {}
        for contract in self.compilation_unit.contracts_derived:
            func_ids.update(get_signatures(contract))
        # todo: include func_ids from the public db

        results = []
        for contract in self.compilation_unit.contracts_derived:
            for func, node in check_contract(contract, func_ids):
                info = [
                    func,
                    " calls abi.encodeWithSelector() with arguments of incorrect type or with an incorrect number of arguments:",
                    node,
                ]
                json = self.generate_result(info)
                results.append(json)

        return results


def check_wrong_selector_encoding(
    function: Function, node: Node, ir: Operation, func_ids: Dict[str, str]
) -> List[Tuple[Function, Node]]:
    result = []
    if isinstance(ir, SolidityCall) and ir.function == SolidityFunction("abi.encodeWithSelector()"):
        # build reference bindings dict
        assignments = {}
        for ir1 in node.irs:
            if isinstance(ir1, Assignment):
                assignments[ir1.lvalue.name] = ir1.rvalue

        # if the selector is a reference, deref
        selector = ir.arguments[0]
        if isinstance(selector, ReferenceVariable):
            selector = assignments[selector.name]

        # Does not handle LocalVariables
        if not isinstance(selector, Constant):
            if isinstance(selector.expression, TypeConversion) and isinstance(
                selector.expression.expression, Literal
            ):
                selector = selector.expression.expression.value
            else:
                return result

        _, _, argument_types = func_ids[selector.value]
        arguments = ir.arguments[1:]

        # todo: add check for user defined types
        if len(argument_types) != len(arguments):
            result.append((function, node))
        else:
            for idx, expected in enumerate(argument_types):
                if expected != str(arguments[idx].type):
                    result.append((function, node))
                    break

    return result


def check_contract(contract: Contract, func_ids: Dict[str, str]) -> List[Tuple[Function, Node]]:
    """Check contract's usage of abi.encodeWithSelector to ensure that the number of arguments
    and their type math the function signature of the given selector.
    """
    result = []
    for function in contract.functions_and_modifiers_declared:
        if SolidityFunction("abi.encodeWithSelector()") in function.solidity_calls:
            for node in function.nodes:
                if SolidityFunction("abi.encodeWithSelector()") in node.solidity_calls:
                    for ir in node.irs:
                        result += check_wrong_selector_encoding(function, node, ir, func_ids)

    return result
