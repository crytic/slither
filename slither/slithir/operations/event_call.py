
from slither.slithir.operations.call import Call
from slither.core.variables.variable import Variable

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
        def unroll(l):
            ret = []
            for x in l:
                if not isinstance(x, list):
                    ret += [x]
                else:
                    ret += unroll(x)
            return ret
        return unroll(self.arguments)

    def __str__(self):
        args = [str(a) for a in self.arguments]
        return 'Emit {}({})'.format(self.name, '.'.join(args))
