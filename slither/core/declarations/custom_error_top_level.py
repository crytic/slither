from typing import TYPE_CHECKING

from slither.core.declarations.custom_error import CustomError
from slither.core.declarations.top_level import TopLevel

if TYPE_CHECKING:
    from slither.core.compilation_unit import SlitherCompilationUnit
    from slither.core.scope.scope import FileScope


class CustomErrorTopLevel(CustomError, TopLevel):
    def __init__(self, compilation_unit: "SlitherCompilationUnit", scope: "FileScope") -> None:
        super().__init__(compilation_unit)
        self.file_scope: "FileScope" = scope

    @property
    def canonical_name(self) -> str:
        return self.full_name
