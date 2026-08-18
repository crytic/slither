from slither.core.source_mapping.source_mapping import SourceMapping
from slither.core.variables.event_variable import EventVariable


class Event(SourceMapping):
    def __init__(self) -> None:
        super().__init__()
        self._name = None
        self._elems: list[EventVariable] = []

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, name: str):
        self._name = name

    @property
    def signature(self) -> tuple[str, list[str]]:
        """Return the function signature
        Returns:
            (str, list(str)): name, list parameters type
        """
        return self.name, [str(x.type) for x in self.elems]

    @property
    def full_name(self) -> str:
        """Return the function signature as a str
        Returns:
            str: func_name(type1,type2)
        """
        name, parameters = self.signature
        return name + "(" + ",".join(parameters) + ")"

    @property
    def elems(self) -> list["EventVariable"]:
        return self._elems

    def __str__(self) -> str:
        return self.name
