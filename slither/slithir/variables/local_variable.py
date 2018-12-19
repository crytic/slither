
from .variable import SlithIRVariable
from slither.core.variables.local_variable import LocalVariable
from slither.core.children.child_node import ChildNode

class LocalIRVariable(LocalVariable, SlithIRVariable):

    def __init__(self, local_variable):
        assert isinstance(local_variable, LocalVariable)

        super(LocalIRVariable, self).__init__()

        # initiate ChildContract
        self.set_function(local_variable.function)

        # initiate Variable
        self._name = local_variable.name
        self._initial_expression = local_variable.expression
        self._type = local_variable.type
        self._initialized = local_variable.initialized
        self._visibility = local_variable.visibility
        self._is_constant = local_variable.is_constant

        # initiate LocalVariable
        self._location = self.location

        self._index = 0

        # Additional field
        # points to state variables
        self._points_to = set()

    @property
    def index(self):
        return self._index

    @index.setter
    def index(self, idx):
        self._index = idx

    @property
    def points_to(self):
        if self.is_storage:
            return self._points_to
        return set()

    @points_to.setter
    def points_to(self, variables):
        self._points_to = variables

    def add_points_to(self, variable):
        assert isinstance(variable, SlithIRVariable)
        self._points_to.add(variable)

    @property
    def ssa_name(self):
        if self.is_storage:
            return '{}_{} (-> {})'.format(self._name,
                                             self.index,
                                             [v.name for v in self.points_to])
        return '{}_{} ({})'.format(self._name, self.index, self.location)
