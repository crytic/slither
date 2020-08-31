from typing import Optional, TYPE_CHECKING

from .variable import SlithIRVariable
from slither.core.variables.state_variable import StateVariable
from slither.slithir.variables.variable import SlithIRVariable

if TYPE_CHECKING:
    from slither.core.solidity_types.type import Type
    from slither.core.expressions.expression import Expression


class StateIRVariable(StateVariable, SlithIRVariable):
    def __init__(self, state_variable: StateVariable):
        assert isinstance(state_variable, StateVariable)

        super(StateVariable, self).__init__()

        # initiate ChildContract
        self.set_contract(state_variable.contract)

        # initiate Variable
        self._name: str = state_variable.name
        self._initial_expression: Optional["Expression"] = state_variable.expression
        self._type: Optional["Type"] = state_variable.type
        self._initialized: Optional[bool] = state_variable.initialized
        self._visibility: Optional[str] = state_variable.visibility
        self._is_constant: bool = state_variable.is_constant

        self._index: int = 0

        # keep un-ssa version
        if isinstance(state_variable, StateIRVariable):
            self._non_ssa_version = state_variable.non_ssa_version
        else:
            self._non_ssa_version = state_variable

    @property
    def index(self) -> int:
        return self._index

    @index.setter
    def index(self, idx):
        self._index = idx

    @property
    def non_ssa_version(self) -> StateVariable:
        return self._non_ssa_version

    @property
    def ssa_name(self) -> str:
        return "{}_{}".format(self._name, self.index)

    def ssa_name(self):
        return "{}_{}".format(self._name, self.index)
