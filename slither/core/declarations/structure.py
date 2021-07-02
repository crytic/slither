from typing import List, TYPE_CHECKING, Dict

from slither.core.source_mapping.source_mapping import SourceMapping

if TYPE_CHECKING:
    from slither.core.variables.structure_variable import StructureVariable


class Structure(SourceMapping):
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

    @property
    def elems_ordered(self) -> List["StructureVariable"]:
        ret = []
        for e in self._elems_ordered:
            ret.append(self._elems[e])
        return ret

    def __str__(self):
        return self.name

    # @webthethird added to resolve false positives in upgradeability > checks > variables_order
    def __eq__(self, other):
        if not isinstance(other, Structure):
            # print(self._name + " != " + other.name + " other is not instance of Structure")
            return False
        if not self.name == other.name:
            # print(self._name + " != " + other.name + " names don't match")
            return False
        elems1 = self.elems_ordered
        elems2 = other.elems_ordered
        if not len(elems1) == len(elems2):
            # print(self._name + " != " + other.name + " lengths don't match")
            return False
        for i in range(len(elems1)):
            if (elems1[i].name != elems2[i].name) or (elems1[i].type != elems2[i].type) \
                                                  or (elems1[i].type.storage_size != elems2[i].type.storage_size):
                # print(self._name + " != " + other.name
                #       + " elems1[" + str(i) + "]: " + str(elems1[i]) + " (" + str(elems1[i].type) + ") !="
                #       + " elems2[" + str(i) + "]: " + str(elems2[i]) + " (" + str(elems2[i].type) + ")")
                return False
        return True
