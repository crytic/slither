from slither.core.variables.local_variable import LocalVariable

class LocalVariableInitFromTuple(LocalVariable):
    """
        Use on this pattern:
        var(a,b) = f()

        It is not possible to split the variable declaration in sigleton and keep the init value
        We init a and b with f(). get_tuple_index ret() returns which returns values of f is to be used

    """

    def __init__(self):
        super(LocalVariableInitFromTuple, self).__init__()
        self._tuple_index = None

    @property
    def tuple_index(self):
        return self._tuple_index
