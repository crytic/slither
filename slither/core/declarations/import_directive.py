from pathlib import Path
from typing import Optional, TYPE_CHECKING, Dict

from slither.core.source_mapping.source_mapping import SourceMapping

if TYPE_CHECKING:
    from slither.core.scope.scope import FileScope


class Import(SourceMapping):
    def __init__(self, filename: Path, scope: "FileScope"):
        super().__init__()
        self._filename: Path = filename
        self._alias: Optional[str] = None
        self.scope: "FileScope" = scope
        # Map local name -> original name
        self.renaming: Dict[str, str] = {}

    @property
    def filename(self) -> str:
        """
        Return the absolute filename

        :return:
        :rtype:
        """
        return str(self._filename)

    @property
    def filename_path(self) -> Path:
        """
        Return the absolute filename

        :return:
        :rtype:
        """

        return self._filename

    @property
    def alias(self) -> Optional[str]:
        return self._alias

    @alias.setter
    def alias(self, a: str):
        self._alias = a

    def __str__(self):
        return self.filename
