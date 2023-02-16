from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from slither.core.declarations import Function


class ChildFunction:
    def __init__(self) -> None:
        super().__init__()
        # TODO remove all the setters for the child objects
        # And make it a constructor arguement
        # This will remove the optional
        self._function: Optional["Function"] = None

    def set_function(self, function: "Function") -> None:
        self._function = function

    @property
    def function(self) -> "Function":
        return self._function  # type: ignore
