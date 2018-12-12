from slither.slithir.operations.operation import Operation

from slither.slithir.variables.tuple import TupleVariable
from slither.slithir.utils.utils import is_valid_rvalue
class Return(Operation):
    """
       Return
       Only present as last operation in RETURN node
    """
    def __init__(self, values):
        # Note: Can return None 
        # ex: return call()
        # where call() dont return
        if not isinstance(values, list):
            assert is_valid_rvalue(values) or isinstance(values, TupleVariable) or values == None
            if not values is None:
                values = [values]
        else:
            for value in values:
                assert is_valid_rvalue(value) or isinstance(value, TupleVariable)
        super(Return, self).__init__()
        self._values = values

    @property
    def read(self):
        return self.values

    @property
    def values(self):
        return self._values

    def __str__(self):
        return "RETURN {}".format(','.join(['{}'.format(x) for x in self.values]))
