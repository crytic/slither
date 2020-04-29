from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from slither.core.declarations import Event


class ChildEvent:
    def __init__(self):
        super(ChildEvent, self).__init__()
        self._event = None

    def set_event(self, event: "Event"):
        self._event = event

    @property
    def event(self) -> "Event":
        return self._event
