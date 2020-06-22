from typing import List, Tuple, TYPE_CHECKING

from slither.core.children.child_contract import ChildContract
from slither.core.source_mapping.source_mapping import SourceMapping
from slither.core.variables.event_variable import EventVariable

if TYPE_CHECKING:
    from slither.core.declarations import Contract


class Event(ChildContract, SourceMapping):
    def __init__(self):
        super(Event, self).__init__()
        self._name = None
        self._elems: List[EventVariable] = []

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, name: str):
        self._name = name

    @property
    def signature(self) -> Tuple[str, List[str]]:
        """ Return the function signature
        Returns:
            (str, list(str)): name, list parameters type
        """
        return self.name, [str(x.type) for x in self.elems]

    @property
    def full_name(self) -> str:
        """ Return the function signature as a str
        Returns:
            str: func_name(type1,type2)
        """
        name, parameters = self.signature
        return name + "(" + ",".join(parameters) + ")"

    @property
    def canonical_name(self) -> str:
        """ Return the function signature as a str
        Returns:
            str: contract.func_name(type1,type2)
        """
        return self.contract.name + self.full_name

    @property
    def elems(self) -> List["EventVariable"]:
        return self._elems

    def is_declared_by(self, contract: "Contract") -> bool:
        """
        Check if the element is declared by the contract
        :param contract:
        :return:
        """
        return self.contract == contract

    def __str__(self):
        return self.name
