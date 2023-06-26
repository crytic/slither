from slither.core.variables.state_variable import StateVariable
from slither.slithir.variables.variable import SlithIRVariable


class StateIRVariable(
    StateVariable, SlithIRVariable
):  # pylint: disable=too-many-instance-attributes
    def __init__(self, state_variable: StateVariable) -> None:
        assert isinstance(state_variable, StateVariable)

        super().__init__()

        # initiate ChildContract
        self.set_contract(state_variable.contract)

        # initiate Variable
        self._name = state_variable.name
        self._initial_expression = state_variable.expression
        self._type = state_variable.type
        self._initialized = state_variable.initialized
        self._visibility = state_variable.visibility
        self._is_constant = state_variable.is_constant

        self._index = 0

        # keep un-ssa version
        if isinstance(state_variable, StateIRVariable):
            self._non_ssa_version = state_variable.non_ssa_version
        else:
            self._non_ssa_version = state_variable

    @property
    def index(self) -> int:
        return self._index

    @index.setter
    def index(self, idx: int) -> None:
        self._index = idx

    @property
    def non_ssa_version(self) -> StateVariable:
        return self._non_ssa_version

    @property
    def ssa_name(self):
        return f"{self._name}_{self.index}"
