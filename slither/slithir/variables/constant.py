from functools import total_ordering
from decimal import Decimal

from .variable import SlithIRVariable
from slither.core.solidity_types.elementary_type import ElementaryType, Int, Uint
from slither.utils.arithmetic import convert_subdenomination

@total_ordering
class Constant(SlithIRVariable):

    def __init__(self, val, type=None, subdenomination=None):
        super(Constant, self).__init__()
        assert isinstance(val, str)

        self._original_value = val
        self._subdenomination = subdenomination

        if subdenomination:
            val = str(convert_subdenomination(val, subdenomination))

        if type:
            assert isinstance(type, ElementaryType)
            self._type = type
            if type.type in Int + Uint + ['address']:
                if val.startswith('0x') or val.startswith('0X'):
                    self._val = int(val, 16)
                else:
                    if 'e' in val:
                        base, expo = val.split('e')
                        self._val = int(Decimal(base) * (10 ** int(expo)))
                    elif 'E' in val:
                        base, expo = val.split('E')
                        self._val = int(Decimal(base) * (10 ** int(expo)))
                    else:
                        self._val = int(Decimal(val))
            elif type.type == 'bool':
                self._val = (val == 'true') | (val == 'True')
            else:
                self._val = val
        else:
            if val.isdigit():
                self._type = ElementaryType('uint256')
                self._val = int(Decimal(val))
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

    def __ne__(self, other):
        return self.value != other

    def __lt__(self, other):
        return self.value < other

    def __repr__(self):
        return "%s" % (str(self.value))