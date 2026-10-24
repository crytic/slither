"""Regression test for #2839: a Yul function must not shadow a contract function
when resolving a high-level call."""

from slither.core.declarations.function import FunctionLanguage
from slither.slithir.operations import HighLevelCall

SOURCE = """
contract State {
    function f() public returns (uint) {
        assembly {
            function f() {}
        }
        return 0;
    }
}

contract C {
    uint y;

    State s;

    function f() public {
        y = s.f();
    }
}
"""


def test_high_level_call_ignores_yul_function(slither_from_solidity_source) -> None:
    with slither_from_solidity_source(SOURCE) as slither:
        caller = slither.get_contract_from_name("C")[0].get_function_from_signature("f()")
        calls = [op for op in caller.slithir_operations if isinstance(op, HighLevelCall)]

        assert len(calls) == 1
        assert calls[0].function is not None
        assert calls[0].function.canonical_name == "State.f()"
        assert calls[0].function.function_language is FunctionLanguage.Solidity
