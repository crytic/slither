from typing import TYPE_CHECKING

from slither.core.declarations import Structure
from slither.core.declarations.top_level import TopLevel

if TYPE_CHECKING:
    from slither.core.scope.scope import FileScope
    from slither.core.compilation_unit import SlitherCompilationUnit


class StructureTopLevel(Structure, TopLevel):
    def __init__(self, compilation_unit: "SlitherCompilationUnit", scope: "FileScope"):
        super().__init__(compilation_unit)
        self.file_scope: "FileScope" = scope
