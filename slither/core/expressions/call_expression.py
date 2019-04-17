from slither.core.expressions.expression import Expression

class CallExpression(Expression):

    def __init__(self, called, arguments, type_call, src=""):
        assert isinstance(called, Expression)
        super(CallExpression, self).__init__()
        self._called = called
        self._arguments = arguments
        self._type_call = type_call
        self._src = src

    @property
    def called(self):
        return self._called

    @property
    def arguments(self):
        return self._arguments

    @property
    def type_call(self):
        return self._type_call

    @property
    def src(self):
        return self._src

    def __str__(self):
        return str(self._called) + '(' + ','.join([str(a) for a in self._arguments]) + ')'
