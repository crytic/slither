from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from slither.core.declarations import Event


class ChildEvent:
    def __init__(self) -> None:
        super().__init__()
        # TODO remove all the setters for the child objects
        # And make it a constructor arguement
        # This will remove the optional
        self._event: Optional["Event"] = None

    def set_event(self, event: "Event") -> None:
        self._event = event

    @property
    def event(self) -> "Event":
        return self._event  # type: ignore
