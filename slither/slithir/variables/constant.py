from .variable import SlithIRVariable
from slither.core.solidity_types.elementary_type import ElementaryType, Int, Uint


class Constant(SlithIRVariable):

    def __init__(self, val, type=None):
        super(Constant, self).__init__()
        assert isinstance(val, str)

        self._original_value = val

        if type:
            assert isinstance(type, ElementaryType)
            self._type = type
            if type.type in Int + Uint:
                if val.startswith('0x'):
                    self._val = int(val, 16)
                else:
                    if 'e' in val:
                        base, expo = val.split('e')
                        self._val = int(float(base)* (10 ** int(expo)))
                    elif 'E' in val:
                        base, expo = val.split('E')
                        self._val = int(float(base) * (10 ** int(expo)))
                    else:
                        self._val = int(val)
            elif type.type == 'bool':
                self._val = val == 'true'
            else:
                self._val = val
        else:
            if val.isdigit():
                self._type = ElementaryType('uint256')
                self._val = int(val)
            else:
                self._type = ElementaryType('string')
                self._val = val

    @property
    def value(self):
        '''
        Return the value.
        If the expression was an hexadecimal delcared as hex'...'
        return a str
        Returns:
            (str | int | bool)
        '''
        return self._val

    @property
    def original_value(self):
        '''
        Return the string representation of the value
        :return: str
        '''
        return self._original_value

    def __str__(self):
        return str(self.value)

    @property
    def name(self):
        return str(self)

    def __eq__(self, other):
        return self.value == other
