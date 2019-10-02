
class ChildExpression:
    def __init__(self):
        super(ChildExpression, self).__init__()
        self._expression = None

    def set_expression(self, expression):
        self._expression = expression

    @property
    def expression(self):
        return self._expression
