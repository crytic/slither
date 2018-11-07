
class ChildFunction:
    def __init__(self):
        super(ChildFunction, self).__init__()
        self._function = None

    def set_function(self, function):
        self._function = function

    @property
    def function(self):
        return self._function
