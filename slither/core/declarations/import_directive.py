from pathlib import Path
from typing import TYPE_CHECKING

from slither.core.source_mapping.source_mapping import SourceMapping

if TYPE_CHECKING:
    from slither.core.scope.scope import FileScope


class Import(SourceMapping):
    def __init__(self, filename: Path, scope: "FileScope") -> None:
        super().__init__()
        self._filename: Path = filename
        self.scope: FileScope = scope
        self._alias: str | None = None
        # Map local name -> original name
        self.renaming: dict[str, str] = {}

        self._pattern = "import"

    @property
    def filename(self) -> str:
        """
        Return the absolute filename

        :return:
        :rtype:
        """
        return self._filename.as_posix()

    @property
    def filename_path(self) -> Path:
        """
        Return the absolute filename

        :return:
        :rtype:
        """

        return self._filename

    @property
    def alias(self) -> str | None:
        return self._alias

    @alias.setter
    def alias(self, a: str):
        self._alias = a

    def __str__(self):
        return self.filename
