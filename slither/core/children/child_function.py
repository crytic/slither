from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from slither.core.declarations import Function


class ChildFunction:
    def __init__(self) -> None:
        super().__init__()
        self._function = None

    def set_function(self, function: "Function") -> None:
        self._function = function

    @property
    def function(self) -> "Function":
        return self._function
