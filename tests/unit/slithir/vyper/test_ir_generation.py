# # pylint: disable=too-many-lines
import pathlib
from argparse import ArgumentTypeError
from collections import defaultdict
from inspect import getsourcefile
from typing import Union, List, Dict, Callable

import pytest

from slither import Slither
from slither.core.cfg.node import Node, NodeType
from slither.core.declarations import Function, Contract
from slither.core.solidity_types import ArrayType
from slither.core.variables.local_variable import LocalVariable
from slither.core.variables.state_variable import StateVariable
from slither.slithir.operations import (
    OperationWithLValue,
    Phi,
    Assignment,
    HighLevelCall,
    Return,
    Operation,
    Binary,
    BinaryType,
    InternalCall,
    Index,
    InitArray,
)
from slither.slithir.utils.ssa import is_used_later
from slither.slithir.variables import (
    Constant,
    ReferenceVariable,
    LocalIRVariable,
    StateIRVariable,
    TemporaryVariableSSA,
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
    self.counter = y # tainted by x, 1

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
