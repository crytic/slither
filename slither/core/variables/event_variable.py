from slither.core.variables.variable import Variable


class EventVariable(Variable):
    def __init__(self) -> None:
        super().__init__()
        self._indexed = False

    @property
    def indexed(self) -> bool:
        """
        Indicates whether the event variable is indexed in the bloom filter.
        :return: Returns True if the variable is indexed in bloom filter, False otherwise.
        """
        return self._indexed

    @indexed.setter
    def indexed(self, is_indexed: bool) -> None:
        self._indexed = is_indexed
