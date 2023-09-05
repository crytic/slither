# # pylint: disable=too-many-lines


from slither.core.solidity_types import ElementaryType
from slither.slithir.operations import (
    Phi,
    InternalCall,
)
from slither.slithir.variables import (
    Constant,
)


def test_interface_conversion_and_call_resolution(slither_from_vyper_source):
    with slither_from_vyper_source(
        """
interface Test:
    def foo() -> (int128, uint256): nonpayable

@internal
def foo() -> (int128, int128):
    return 2, 3

@external
def bar():
    a: int128 = 0
    b: int128 = 0
    (a, b) = self.foo()

    x: address = 0x0000000000000000000000000000000000000000
    c: uint256 = 0
    a, c = Test(x).foo()
"""
    ) as sl:
        interface = next(iter(x for x in sl.contracts if x.is_interface))
        contract = next(iter(x for x in sl.contracts if not x.is_interface))
        func = contract.get_function_from_signature("bar()")
        (contract, function) = func.high_level_calls[0]
        assert contract == interface
        assert function.signature_str == "foo() returns(int128,uint256)"


def test_phi_entry_point_internal_call(slither_from_vyper_source):
    with slither_from_vyper_source(
        """
counter: uint256
@internal
def b(y: uint256):
    self.counter = y

@external
def a(x: uint256):
    self.b(x)
    self.b(1)
"""
    ) as sl:
        f = sl.contracts[0].get_function_from_signature("b(uint256)")
        assert (
            len(
                [
                    ssanode
                    for node in f.nodes
                    for ssanode in node.irs_ssa
                    if isinstance(ssanode, Phi)
                ]
            )
            == 1
        )


def test_call_with_default_args(slither_from_vyper_source):
    with slither_from_vyper_source(
        """
counter: uint256
@internal
def c(y: uint256, config: bool = True):
    self.counter = y
@external
def a(x: uint256):
    self.c(x)
    self.c(1)
@external
def b(x: uint256):
    self.c(x, False)
    self.c(1, False)
"""
    ) as sl:
        a = sl.contracts[0].get_function_from_signature("a(uint256)")
        for node in a.nodes:
            for op in node.irs_ssa:
                if isinstance(op, InternalCall) and op.function.name == "c":
                    assert len(op.arguments) == 2
                    assert op.arguments[1] == Constant("True", ElementaryType("bool"))
        b = sl.contracts[0].get_function_from_signature("b(uint256)")
        for node in b.nodes:
            for op in node.irs_ssa:
                if isinstance(op, InternalCall) and op.function.name == "c":
                    assert len(op.arguments) == 2
                    assert op.arguments[1] == Constant("False", ElementaryType("bool"))
