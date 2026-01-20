from slither.core.declarations import SolidityFunction
from slither.core.expressions.identifier import Identifier


def test_vyper_external_calls_classification(slither_from_vyper_source):
    source = """
@internal
def foo():
    pass

@external
def test(a: address):
    self.foo()
    raw_call(a, b"")
    send(a, 1)
    x: bytes32 = keccak256(b"")
"""
    with slither_from_vyper_source(source) as sl:
        contract = sl.contracts[0]
        func = contract.get_function_from_signature("test(address)")

        external_called = [
            str(call_expr.called) for call_expr in func.external_calls_as_expressions
        ]
        assert any("raw_call" in name for name in external_called)
        assert any("send" in name for name in external_called)

        internal_calls = [
            call_expr for node in func.nodes for call_expr in node.internal_calls_as_expressions
        ]
        internal_called = [str(call_expr.called) for call_expr in internal_calls]
        assert any("self.foo" in name for name in internal_called)
        assert any("keccak256" in name for name in internal_called)


def test_yul_external_calls_classification(slither_from_solidity_source):
    source = """
pragma solidity ^0.8.19;

contract Test {
    function yulCalls(address target) external {
        assembly {
            let g := gas()
            let c := call(g, target, 0, 0, 0, 0, 0)
            let cc := callcode(g, target, 0, 0, 0, 0, 0)
            let d := delegatecall(g, target, 0, 0, 0, 0)
            let s := staticcall(g, target, 0, 0, 0, 0)
            pop(c)
            pop(cc)
            pop(d)
            pop(s)
        }
    }
}
"""
    with slither_from_solidity_source(source) as sl:
        contract = sl.contracts[0]
        func = contract.get_function_from_signature("yulCalls(address)")

        external_names = set()
        for call in func.external_calls_as_expressions:
            called = call.called
            assert isinstance(called, Identifier)
            assert isinstance(called.value, SolidityFunction)
            external_names.add(called.value.name.split("(")[0])

        assert external_names == {"call", "callcode", "delegatecall", "staticcall"}
