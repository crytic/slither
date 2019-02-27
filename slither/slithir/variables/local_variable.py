
from .variable import SlithIRVariable
from .temporary import TemporaryVariable
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
        self._location = local_variable.location
        self._is_storage = local_variable.is_storage

        self._index = 0

        # Additional field
        # points to state variables
        self._refers_to = set()

        # keep un-ssa version
        if isinstance(local_variable, LocalIRVariable):
            self._non_ssa_version = local_variable.non_ssa_version
        else:
            self._non_ssa_version = local_variable

    @property
    def index(self):
        return self._index

    @index.setter
    def index(self, idx):
        self._index = idx

    @property
    def refers_to(self):
        if self.is_storage:
            return self._refers_to
        return set()

    @refers_to.setter
    def refers_to(self, variables):
        self._refers_to = variables

    @property
    def non_ssa_version(self):
        return self._non_ssa_version

    def add_refers_to(self, variable):
        # It is a temporaryVariable if its the return of a new ..
        # ex: string[] memory dynargs = new string[](1);
        assert isinstance(variable, (SlithIRVariable, TemporaryVariable))
        self._refers_to.add(variable)

    @property
    def ssa_name(self):
        if self.is_storage:
            return '{}_{} (-> {})'.format(self._name,
                                             self.index,
                                             [v.name for v in self.refers_to])
        return '{}_{}'.format(self._name, self.index)
