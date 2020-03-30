from slither.core.expressions.expression import Expression


class CallExpression(Expression):

    def __init__(self, called, arguments, type_call):
        assert isinstance(called, Expression)
        super(CallExpression, self).__init__()
        self._called = called
        self._arguments = arguments
        self._type_call = type_call
        # gas and value are only available if the syntax is {gas: , value: }
        # For the .gas().value(), the member are considered as function call
        # And converted later to the correct info (convert.py)
        self._gas = None
        self._value = None

    @property
    def call_value(self):
        return self._value

    @call_value.setter
    def call_value(self, v):
        self._value = v

    @property
    def call_gas(self):
        return self._gas

    @call_gas.setter
    def call_gas(self, gas):
        self._gas = gas

    @property
    def called(self):
        return self._called

    @property
    def arguments(self):
        return self._arguments

    @property
    def type_call(self):
        return self._type_call

    def __str__(self):
        txt = str(self._called)
        if self.call_gas or self.call_value:
            gas = f'gas: {self.call_gas}' if self.call_gas else ''
            value = f'value: {self.call_value}' if self.call_value else ''
            if gas and value:
                txt += '{' + f'{gas}, {value}' + '}'
            elif gas:
                txt += '{' + f'{gas}' + '}'
            else:
                txt += '{' + f'{value}' + '}'
        return txt + '(' + ','.join([str(a) for a in self._arguments]) + ')'
