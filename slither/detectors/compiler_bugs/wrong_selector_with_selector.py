from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.slithir.operations import SolidityCall
from slither.core.declarations.solidity_variables import SolidityFunction
from slither.slithir.operations.assignment import Assignment
from slither.slithir.variables.reference import ReferenceVariable
from slither.slithir.variables.constant import Constant
from slither.utils.function import get_function_id


def get_signatures(c):
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
        result[get_function_id(name)] = (name, (),())

    return result


class WrongEncodeWithSelector(AbstractDetector):
    """
    Detect calls to abi.encodeWithSelector that may result in unexpected calldata encodings
    """

    ARGUMENT = "wrongencodeselector"
    HELP = "abi.encodeWithSelector with unexpected arguments"
    IMPACT = DetectorClassification.MEDIUM
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = "https://github.com/trailofbits/slither/wiki/encode-with-selector"
    WIKI_TITLE = "Parameters of incorrect type in abi.encodeWithSelector"
    WIKI_DESCRIPTION = "Plugin example"
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
    WIKI_RECOMMENDATION = "Make sure that encodeWithSelector is building a calldata that matches the target function signature"

    def _detect(self):
        #gather all known funcids
        func_ids = {}
        for contract in self.contracts:
            func_ids.update(get_signatures(contract))
        #todo: include func_ids from the public db

        results = []
        for contract in self.contracts:
            for func, node in check_contract(contract, func_ids):
                info = [func, " calls abi.encodeWithSelector() with arguments of incorrect type:", node ]
                json = self.generate_result(info)
                results.append(json)

        return results

def check_ir(function, node, ir, func_ids):
    result = []
    if isinstance(ir, SolidityCall) and ir.function == SolidityFunction(
            "abi.encodeWithSelector()"
    ):

        # build reference bindings dict
        assignments = {}
        for ir1 in node.irs:
            if isinstance(ir1, Assignment):
                assignments[ir1.lvalue.name] = ir1.rvalue

        # if the selector is a reference, deref
        selector = ir.arguments[0]
        if isinstance(selector, ReferenceVariable):
            selector = assignments[selector.name]

        assert isinstance(selector, Constant)

        _, _, argument_types = func_ids[selector.value]
        arguments = ir.arguments[1:]

        if len(argument_types) != len(arguments):
            result.append((function, node))

        # Todo check_contract unmatching argument types for correct count
    return result

def check_contract(contract, func_ids):
    """ check_contract if contract has an ecodeWhitSelector that uses a selector
        for a method with an unmatching number of arguments
    """
    result = []
    for function in contract.functions_and_modifiers_declared:
        for node in function.nodes:
            for ir in node.irs:
                result += check_ir(function, node, ir, func_ids)

    return result
