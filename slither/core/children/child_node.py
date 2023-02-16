from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from slither.core.compilation_unit import SlitherCompilationUnit
    from slither.core.cfg.node import Node
    from slither.core.declarations import Function, Contract


class ChildNode:
    def __init__(self) -> None:
        super().__init__()
        # TODO remove all the setters for the child objects
        # And make it a constructor arguement
        # This will remove the optional
        self._node: Optional["Node"] = None

    def set_node(self, node: "Node") -> None:
        self._node = node

    @property
    def node(self) -> "Node":
        return self._node  # type:ignore

    @property
    def function(self) -> "Function":
        return self.node.function

    @property
    def contract(self) -> "Contract":
        return self.node.function.contract  # type: ignore

    @property
    def compilation_unit(self) -> "SlitherCompilationUnit":
        return self.node.compilation_unit
