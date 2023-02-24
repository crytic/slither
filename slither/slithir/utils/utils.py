from typing import Union, Optional

from slither.core.variables.local_variable import LocalVariable
from slither.core.variables.state_variable import StateVariable

from slither.core.declarations.solidity_variables import SolidityVariable
from slither.core.variables.top_level_variable import TopLevelVariable

from slither.slithir.variables.temporary import TemporaryVariable
from slither.slithir.variables.constant import Constant
from slither.slithir.variables.reference import ReferenceVariable
from slither.slithir.variables.tuple import TupleVariable
from slither.core.source_mapping.source_mapping import SourceMapping

RVALUE = Union[
    StateVariable,
    LocalVariable,
    TopLevelVariable,
    TemporaryVariable,
    Constant,
    SolidityVariable,
    ReferenceVariable,
]

LVALUE = Union[
    StateVariable,
    LocalVariable,
    TemporaryVariable,
    ReferenceVariable,
    TupleVariable,
]


def is_valid_rvalue(v: Optional[SourceMapping]) -> bool:
    return isinstance(
        v,
        (
            StateVariable,
            LocalVariable,
            TopLevelVariable,
            TemporaryVariable,
            Constant,
            SolidityVariable,
            ReferenceVariable,
        ),
    )


def is_valid_lvalue(v: Optional[SourceMapping]) -> bool:
    return isinstance(
        v,
        (
            StateVariable,
            LocalVariable,
            TemporaryVariable,
            ReferenceVariable,
            TupleVariable,
        ),
    )
