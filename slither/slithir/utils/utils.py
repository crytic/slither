from typing import Union

from slither.core.variables.local_variable import LocalVariable
from slither.core.variables.state_variable import StateVariable

from slither.core.declarations.solidity_variables import SolidityVariable

from slither.slithir.variables.temporary import TemporaryVariable
from slither.slithir.variables.constant import Constant
from slither.slithir.variables.index_variable import IndexVariable
from slither.slithir.variables.member_variable import MemberVariable
from slither.slithir.variables.tuple import TupleVariable


VALID_RVALUE = Union[
    StateVariable,
    LocalVariable,
    TemporaryVariable,
    Constant,
    SolidityVariable,
    IndexVariable,
    MemberVariable,
]


def is_valid_rvalue(v):
    return isinstance(
        v,
        (
            StateVariable,
            LocalVariable,
            TemporaryVariable,
            Constant,
            SolidityVariable,
            IndexVariable,
            MemberVariable,
        ),
    )


VALID_LVALUE = Union[
    StateVariable, LocalVariable, TemporaryVariable, IndexVariable, MemberVariable, TupleVariable
]


def is_valid_lvalue(v):
    return isinstance(
        v,
        (
            StateVariable,
            LocalVariable,
            TemporaryVariable,
            IndexVariable,
            MemberVariable,
            TupleVariable,
        ),
    )
