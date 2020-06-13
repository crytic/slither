from typing import List

from slither.slithir.operations.call import Call


class EventCall(Call):
    def __init__(self, name: str):
        super(EventCall, self).__init__()
        self._name: str = name
        # todo add instance of the Event

    @property
    def name(self) -> str:
        return self._name

    @property
    def read(self) -> List:
        return self._unroll(self.arguments)

    def __str__(self):
        args = [str(a) for a in self.arguments]
        return "Emit {}({})".format(self.name, ".".join(args))
