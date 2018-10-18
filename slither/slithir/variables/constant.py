from slither.core.variables.variable import Variable

class Constant(Variable):

    def __init__(self, val):
        super(Constant, self).__init__()
        assert isinstance(val, str)
        if val.isdigit():
            self._type = 'uint256'
            self._val = int(val)
        else:
            self._type = 'string'
            self._val = val

    @property
    def value(self):
        '''
        Return the value.
        If the expression was an hexadecimal delcared as hex'...'
        return a str
        Returns:
            (str, int)
        '''
        return self._val

    def __str__(self):
        return str(self.value)


    def __eq__(self, other):
        return self.value == other
