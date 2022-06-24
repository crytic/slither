from slither.slithir.operations.call import Call


class EventCall(Call):
    def __init__(self, destination):
        super().__init__()
        self._destination = destination

    @property
    def destination(self):
        return self._destination

    @property
    def name(self):
        return self.destination.name

    @property
    def read(self):
        return self._unroll(self.arguments)

    def __str__(self):
        args = [str(a) for a in self.arguments]
        return f"Emit {self.name}({'.'.join(args)})"
