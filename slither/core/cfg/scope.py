from typing import List, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from slither.core.cfg.node import Node
    from slither.core.declarations.function import Function


# pylint: disable=too-few-public-methods
class Scope:
    def __init__(self, is_checked: bool, is_yul: bool, scope: Union["Scope", "Function"]):
        self.nodes: List["Node"] = []
        self.is_checked = is_checked
        self.is_yul = is_yul
        self.father = scope
