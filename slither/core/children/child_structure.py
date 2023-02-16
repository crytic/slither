from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from slither.core.declarations import Structure


class ChildStructure:
    def __init__(self) -> None:
        super().__init__()
        # TODO remove all the setters for the child objects
        # And make it a constructor arguement
        # This will remove the optional
        self._structure: Optional["Structure"] = None

    def set_structure(self, structure: "Structure") -> None:
        self._structure = structure

    @property
    def structure(self) -> "Structure":
        return self._structure  # type: ignore
