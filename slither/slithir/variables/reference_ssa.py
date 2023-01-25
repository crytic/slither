"""
    This class is used for the SSA version of slithIR
    It is similar to the non-SSA version of slithIR
    as the ReferenceVariable are in SSA form in both version
"""
from typing import Union
from slither.slithir.variables.reference import ReferenceVariable
from slither.slithir.variables.tuple import TupleVariable


class ReferenceVariableSSA(ReferenceVariable):  # pylint: disable=too-few-public-methods
    def __init__(self, reference: ReferenceVariable) -> None:
        super().__init__(reference.node, reference.index)

        self._non_ssa_version = reference

    @property
    def non_ssa_version(self) -> Union[ReferenceVariable, TupleVariable]:
        return self._non_ssa_version
