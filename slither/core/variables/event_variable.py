from .variable import Variable
from slither.core.children.child_event import ChildEvent

class EventVariable(ChildEvent, Variable):
    def __init__(self):
        super(EventVariable, self).__init__()
        self._indexed = False

    @property
    def indexed(self):
        """
        Indicates whether the event variable is indexed in the bloom filter.
        :return: Returns True if the variable is indexed in bloom filter, False otherwise.
        """
        return self._indexed

