from typing import TYPE_CHECKING

from slither.core.declarations import Event
from slither.core.declarations.top_level import TopLevel

if TYPE_CHECKING:
    from slither.core.scope.scope import FileScope


class EventTopLevel(Event, TopLevel):
    def __init__(self, scope: "FileScope") -> None:
        super().__init__()
        self.file_scope: "FileScope" = scope
