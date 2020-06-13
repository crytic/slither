from typing import Optional, Union, List, TYPE_CHECKING

from slither.slithir.operations.operation import Operation

from slither.slithir.variables.tuple import TupleVariable
from slither.slithir.utils.utils import is_valid_rvalue

if TYPE_CHECKING:
    from slither.slithir.utils.utils import VALID_RVALUE


class Return(Operation):
    """
       Return
       Only present as last operation in RETURN node
    """

    def __init__(
        self, values: Optional[Union["VALID_RVALUE", TupleVariable, List["VALID_RVALUE"]]]
    ):
        # Note: Can return None
        # ex: return call()
        # where call() dont return
        if not isinstance(values, list):
            assert is_valid_rvalue(values) or isinstance(values, TupleVariable) or values is None
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
        super(Return, self).__init__()
        self._values = values

    def _valid_value(self, value):
        if isinstance(value, list):
            assert all(self._valid_value(v) for v in value)
        else:
            assert is_valid_rvalue(value) or isinstance(value, TupleVariable)
        return True

    @property
    def read(self) -> List[Union["VALID_RVALUE", TupleVariable]]:
        return self._unroll(self.values)

    @property
    def values(self) -> List[Union["VALID_RVALUE", TupleVariable]]:
        return self._unroll(self._values)

    def __str__(self):
        return "RETURN {}".format(",".join(["{}".format(x) for x in self.values]))
