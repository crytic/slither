
from .variable import SlithIRVariable
from slither.core.variables.state_variable import StateVariable
from slither.core.children.child_node import ChildNode

class StateIRVariable(StateVariable, SlithIRVariable):

    def __init__(self, state_variable):
        assert isinstance(state_variable, StateVariable)

        super(StateVariable, self).__init__()

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

    @property
    def index(self):
        return self._index

    @index.setter
    def index(self, idx):
        self._index = idx

    @property
    def ssa_name(self):
        return '{}_{}'.format(self._name, self.index)
