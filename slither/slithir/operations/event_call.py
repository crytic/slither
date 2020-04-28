from slither.slithir.operations.call import Call


class EventCall(Call):
    def __init__(self, name):
        super(EventCall, self).__init__()
        self._name = name
        # todo add instance of the Event

    @property
    def name(self):
        return self._name

    @property
    def read(self):
        return self._unroll(self.arguments)

    def __str__(self):
        args = [str(a) for a in self.arguments]
        return "Emit {}({})".format(self.name, ".".join(args))
