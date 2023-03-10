from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from slither.core.declarations import Structure


class ChildStructure:
    def __init__(self) -> None:
        super().__init__()
        self._structure = None

    def set_structure(self, structure: "Structure") -> None:
        self._structure = structure

    @property
    def structure(self) -> "Structure":
        return self._structure
