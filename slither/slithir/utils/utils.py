from slither.core.variables.local_variable import LocalVariable
from slither.core.variables.state_variable import StateVariable

from slither.core.declarations.solidity_variables import SolidityVariable

from slither.slithir.variables.temporary import TemporaryVariable
from slither.slithir.variables.constant import Constant
from slither.slithir.variables.reference import ReferenceVariable
from slither.slithir.variables.tuple import TupleVariable


def is_valid_rvalue(v):
    return isinstance(
        v,
        (
            StateVariable,
            LocalVariable,
            TemporaryVariable,
            Constant,
            SolidityVariable,
            ReferenceVariable,
        ),
    )


def is_valid_lvalue(v):
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
