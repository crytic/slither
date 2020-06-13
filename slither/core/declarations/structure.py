from typing import List, TYPE_CHECKING, Dict

from slither.core.children.child_contract import ChildContract
from slither.core.source_mapping.source_mapping import SourceMapping

if TYPE_CHECKING:
    from slither.core.variables.structure_variable import StructureVariable


class Structure(ChildContract, SourceMapping):
    def __init__(self):
        super(Structure, self).__init__()
        self._name = None
        self._canonical_name = None
        self._elems: Dict[str, "StructureVariable"] = dict()
        # Name of the elements in the order of declaration
        self._elems_ordered: List[str] = []

    @property
    def canonical_name(self) -> str:
        return self._canonical_name

    @property
    def name(self) -> str:
        return self._name

    @property
    def elems(self) -> Dict[str, "StructureVariable"]:
        return self._elems

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
