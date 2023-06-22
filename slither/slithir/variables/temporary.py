from typing import Optional, TYPE_CHECKING

from slither.core.variables.variable import Variable

if TYPE_CHECKING:
    from slither.core.cfg.node import Node


class TemporaryVariable(Variable):
    def __init__(self, node: "Node", index: Optional[int] = None) -> None:
        super().__init__()
        if index is None:
            self._index = node.compilation_unit.counter_slithir_temporary
            node.compilation_unit.counter_slithir_temporary += 1
        else:
            self._index = index
        self._node = node

    @property
    def node(self) -> "Node":
        return self._node

    @property
    def index(self):
        return self._index

    @index.setter
    def index(self, idx):
        self._index = idx

    @property
    def name(self) -> str:
        return f"TMP_{self.index}"

    def __str__(self) -> str:
        return self.name
