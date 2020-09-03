from slither.core.declarations import Function
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
            assert (
                is_valid_rvalue(values)
                or isinstance(values, (TupleVariable, Function))
                or values is None
            )
            if values is None:
                values = []
            else:
                values = [values]
        else:
            # Remove None
            # Prior Solidity 0.5
            # return (0,)
            # was valid for returns(uint)
            values = [v for v in values if not v is None]
            self._valid_value(values)
        super().__init__()
        self._values = values

    def _valid_value(self, value):
        if isinstance(value, list):
            assert all(self._valid_value(v) for v in value)
        else:
            assert is_valid_rvalue(value) or isinstance(value, (TupleVariable, Function))
        return True

    @property
    def read(self):
        return self._unroll(self.values)

    @property
    def values(self):
        return self._unroll(self._values)

    def __str__(self):
        return "RETURN {}".format(",".join(["{}".format(x) for x in self.values]))
