from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from slither.core.declarations import Structure


class ChildStructure:
    def __init__(self):
        super(ChildStructure, self).__init__()
        self._structure = None

    def set_structure(self, structure: "Structure"):
        self._structure = structure

    @property
    def structure(self) -> "Structure":
        return self._structure
