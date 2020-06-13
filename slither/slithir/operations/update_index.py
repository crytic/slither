from typing import TYPE_CHECKING, List

from slither.slithir.operations import Operation
from slither.slithir.utils.utils import is_valid_rvalue

if TYPE_CHECKING:
    from slither.slithir.utils.utils import VALID_RVALUE


class UpdateIndex(Operation):
    def __init__(self, base: "VALID_RVALUE", offset: "VALID_RVALUE", new_val: "VALID_RVALUE"):
        assert is_valid_rvalue(base)
        assert is_valid_rvalue(new_val)
        assert is_valid_rvalue(offset)
        super(UpdateIndex, self).__init__()
        self._base = base
        self._offset = offset
        self._new_val = new_val

    @property
    def read(self) -> List["VALID_RVALUE"]:
        return [self._base, self._new_val]

    @property
    def base(self) -> "VALID_RVALUE":
        return self._base

    @property
    def offset(self) -> "VALID_RVALUE":
        return self._offset

    @property
    def new_value(self) -> "VALID_RVALUE":
        return self._new_val

    def __str__(self):
        return "Update({}, {}, {})".format(self.base, self.offset, self.new_value)
