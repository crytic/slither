from unittest.mock import MagicMock

import pytest

from slither.core.declarations import Contract, SolidityFunction
from slither.core.declarations.solidity_variables import SolidityVariable
from slither.core.expressions.call_expression import CallExpression
from slither.core.expressions.identifier import Identifier
from slither.core.expressions.member_access import MemberAccess
from slither.core.variables.local_variable import LocalVariable
from slither.core.variables.state_variable import StateVariable
from slither.visitors.expression.call_classification import classify_calls


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_member_call(base_value):
    """Build a minimal CallExpression whose callee is a MemberAccess on base_value."""
    base_expr = MagicMock(spec=Identifier)
    base_expr.value = base_value
    called = MagicMock(spec=MemberAccess)
    called.expression = base_expr
    call = MagicMock(spec=CallExpression)
    call.called = called
    return call


def _make_identifier_call(identifier_value):
    """Build a minimal CallExpression whose callee is a plain Identifier."""
    called = MagicMock(spec=Identifier)
    called.value = identifier_value
    call = MagicMock(spec=CallExpression)
    call.called = called
    return call


# ---------------------------------------------------------------------------
# Unit tests for classify_calls (no Solidity compiler required)
# ---------------------------------------------------------------------------


class TestClassifyCalls:
    """Tests for classify_calls with mocked expression objects.

    Covers the cases from https://github.com/crytic/slither/issues/2073:
    Solidity built-ins, library calls, struct/variable member accesses, and
    genuine external contract calls should all be classified correctly.
    """

    def test_abi_encode_is_internal(self):
        """abi.encode() must not appear in external calls (abi is a SolidityVariable)."""
        call = _make_member_call(SolidityVariable("abi"))
        internal, external = classify_calls([call])
        assert call in internal
        assert call not in external

    def test_msg_sender_call_is_internal(self):
        """msg.sender.call() — msg is a SolidityVariable, so the member access is internal."""
        call = _make_member_call(SolidityVariable("msg"))
        internal, external = classify_calls([call])
        assert call in internal
        assert call not in external

    def test_this_call_is_external(self):
        """this.foo() must be classified as external (re-entrant call through the ABI)."""
        call = _make_member_call(SolidityVariable("this"))
        internal, external = classify_calls([call])
        assert call in external
        assert call not in internal

    def test_library_call_is_internal(self):
        """MyLib.foo() must be internal — library calls are inlined at compile time."""
        lib = MagicMock(spec=Contract)
        lib.is_library = True
        call = _make_member_call(lib)
        internal, external = classify_calls([call])
        assert call in internal
        assert call not in external

    def test_non_library_contract_call_is_external(self):
        """ExternalContract.foo() must be external."""
        contract = MagicMock(spec=Contract)
        contract.is_library = False
        call = _make_member_call(contract)
        internal, external = classify_calls([call])
        assert call in external
        assert call not in internal

    def test_state_variable_member_call_is_external(self):
        """token.transfer() where token is a state variable must be external."""
        state_var = MagicMock(spec=StateVariable)
        call = _make_member_call(state_var)
        internal, external = classify_calls([call])
        assert call in external
        assert call not in internal

    def test_plain_identifier_call_is_internal(self):
        """Direct function calls (no member access) must be internal by default."""
        func = MagicMock(spec=SolidityFunction)
        call = _make_identifier_call(func)
        internal, external = classify_calls([call])
        assert call in internal
        assert call not in external

    def test_plain_identifier_call_marked_external(self):
        """is_external_identifier predicate should override identifier classification."""
        func = MagicMock(spec=SolidityFunction)
        call = _make_identifier_call(func)
        called_id = call.called
        internal, external = classify_calls([call], is_external_identifier=lambda x: x is called_id)
        assert call in external
        assert call not in internal

    def test_empty_call_list(self):
        """classify_calls on an empty list must return two empty lists."""
        internal, external = classify_calls([])
        assert internal == []
        assert external == []

    def test_mixed_calls(self):
        """Verify that a mixed list of calls is split correctly."""
        lib = MagicMock(spec=Contract)
        lib.is_library = True
        lib_call = _make_member_call(lib)

        state_var = MagicMock(spec=StateVariable)
        ext_call = _make_member_call(state_var)

        abi_call = _make_member_call(SolidityVariable("abi"))

        internal, external = classify_calls([lib_call, ext_call, abi_call])
        assert lib_call in internal
        assert abi_call in internal
        assert ext_call in external
        assert len(internal) == 2
        assert len(external) == 1


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
