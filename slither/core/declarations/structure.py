from typing import List, TYPE_CHECKING, Dict

from slither.core.children.child_contract import ChildContract
from slither.core.source_mapping.source_mapping import SourceMapping

if TYPE_CHECKING:
    from slither.core.variables.structure_variable import StructureVariable


class Structure(ChildContract, SourceMapping):
    def __init__(self):
        super().__init__()
        self._name = None
        self._canonical_name = None
        self._elems: Dict[str, "StructureVariable"] = dict()
        # Name of the elements in the order of declaration
        self._elems_ordered: List[str] = []

    @property
    def canonical_name(self) -> str:
        return self._canonical_name

    @canonical_name.setter
    def canonical_name(self, name: str):
        self._canonical_name = name

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, new_name: str):
        self._name = new_name

    @property
    def elems(self) -> Dict[str, "StructureVariable"]:
        return self._elems

    def add_elem_in_order(self, s: str):
        self._elems_ordered.append(s)

    def is_declared_by(self, contract):
        """
        Check if the element is declared by the contract
        :param contract:
        :return:
        """
        return self.contract == contract

    @property
    def elems_ordered(self) -> List["StructureVariable"]:
        ret = []
        for e in self._elems_ordered:
            ret.append(self._elems[e])
        return ret

    def __str__(self):
        return self.name
