from typing import List, Optional, Union, Any

from slither.core.declarations import Function
from slither.core.variables.variable import Variable
from slither.slithir.operations.operation import Operation
from slither.slithir.utils.utils import is_valid_rvalue, RVALUE
from slither.slithir.variables.tuple import TupleVariable


class Return(Operation):
    """
    Return
    Only present as last operation in RETURN node
    """

    def __init__(
        self, values: Optional[Union[RVALUE, TupleVariable, Function, List[RVALUE]]]
    ) -> None:
        # Note: Can return None
        # ex: return call()
        # where call() dont return
        self._values: List[Union[RVALUE, TupleVariable, Function]]
        if not isinstance(values, list):
            assert (
                is_valid_rvalue(values)
                or isinstance(values, (TupleVariable, Function))
                or values is None
            )
            if values is None:
                self._values = []
            else:
                self._values = [values]
        else:
            # Remove None
            # Prior Solidity 0.5
            # return (0,)
            # was valid for returns(uint)
            self._values = [v for v in values if not v is None]
            self._valid_value(self._values)
        super().__init__()

    def _valid_value(self, value: Any) -> bool:
        if isinstance(value, list):
            assert all(self._valid_value(v) for v in value)
        else:
            assert is_valid_rvalue(value) or isinstance(value, (TupleVariable, Function))
        return True

    @property
    def read(self) -> List[Variable]:
        return self._unroll(self.values)

    @property
    def values(self) -> List[Variable]:
        return self._unroll(self._values)

    def __str__(self) -> str:
        return f"RETURN {','.join([f'{x}' for x in self.values])}"
