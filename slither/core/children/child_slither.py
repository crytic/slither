from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from slither import Slither


class ChildSlither:
    def __init__(self):
        super().__init__()
        self._slither = None

    def set_slither(self, slither: "Slither"):
        self._slither = slither

    @property
    def slither(self) -> "Slither":
        return self._slither
