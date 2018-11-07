from slither.slithir.operations.operation import Operation

from slither.slithir.variables.tuple import TupleVariable
from slither.slithir.utils.utils import is_valid_rvalue
class Return(Operation):
    """
       Return
       Only present as last operation in RETURN node
    """
    def __init__(self, value):
        # Note: Can return None 
        # ex: return call()
        # where call() dont return
        assert is_valid_rvalue(value) or isinstance(value, TupleVariable) or value == None
        super(Return, self).__init__()
        self._value = value

    @property
    def read(self):
        return [self.value]

    @property
    def value(self):
        return self._value

    def __str__(self):
        return "RETURN {}".format(self.value)
