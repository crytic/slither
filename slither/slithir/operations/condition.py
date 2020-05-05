from typing import TYPE_CHECKING, List

from slither.slithir.operations.operation import Operation

from slither.slithir.utils.utils import is_valid_rvalue

if TYPE_CHECKING:
    from slither.slithir.utils.utils import VALID_RVALUE


class Condition(Operation):
    """
       Condition
       Only present as last operation in conditional node
    """

    def __init__(self, value: "VALID_RVALUE"):
        assert is_valid_rvalue(value)
        super(Condition, self).__init__()
        self._value: "VALID_RVALUE" = value

    @property
    def read(self) -> List["VALID_RVALUE"]:
        return [self.value]

    @property
    def value(self) -> "VALID_RVALUE":
        return self._value

    def __str__(self):
        return "CONDITION {}".format(self.value)
