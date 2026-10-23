#


from slither.core.solidity_types import ElementaryType
from slither.detectors.statements.type_based_tautology import TypeBasedTautology
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
        (contract, ir) = func.high_level_calls[0]
        assert contract == interface
        assert ir.function.signature_str == "foo() returns(int128,uint256)"


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


def test_for_loop_bounds_and_range_start(slither_from_vyper_source):
    with slither_from_vyper_source(
        """
@external
def loop(values: DynArray[uint256, 3]):
    total: uint256 = 0
    for value in values:
        total += value
    for i in range(5, 7):
        total += i
"""
    ) as sl:
        function = next(
            function for function in sl.contracts[0].functions if function.name == "loop"
        )
        cfg = function.slithir_cfg_to_dot_str()

        assert "counter_var < len()(values)" in cfg
        assert "counter_var = 0" in cfg
        assert "counter_var < 7" in cfg
        assert "counter_var_scope_0 = 5" in cfg


def test_range_with_bound_keyword(slither_from_vyper_source):
    with slither_from_vyper_source(
        """
@external
def loop(end: uint256):
    total: uint256 = 0
    for i in range(end, bound=10):
        total += i
"""
    ) as sl:
        function = sl.contracts[0].get_function_from_signature("loop(uint256)")
        cfg = function.slithir_cfg_to_dot_str()

        assert "counter_var = 0" in cfg
        assert "counter_var < end" in cfg
        assert "counter_var = end" not in cfg
        assert "counter_var < 10" not in cfg


def test_range_with_runtime_start(slither_from_vyper_source):
    with slither_from_vyper_source(
        """
@external
def loop(start: uint256):
    total: uint256 = 0
    for i in range(start, start + 5):
        total += i
"""
    ) as sl:
        function = sl.contracts[0].get_function_from_signature("loop(uint256)")
        cfg = function.slithir_cfg_to_dot_str()

        assert "counter_var = start" in cfg
        assert "counter_var < start + 5" in cfg


def test_range_with_negative_start_does_not_trigger_tautology(slither_from_vyper_source):
    with slither_from_vyper_source(
        """
@external
def loop():
    total: int256 = 0
    for i in range(-3, 2):
        total += i
"""
    ) as sl:
        function = sl.contracts[0].get_function_from_signature("loop()")
        cfg = function.slithir_cfg_to_dot_str()

        assert "counter_var = -3" in cfg
        assert "counter_var < 2" in cfg

        sl.register_detector(TypeBasedTautology)
        assert sl.run_detectors() == [[]]
