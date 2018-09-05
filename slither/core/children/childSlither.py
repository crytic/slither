
class ChildSlither(object):

    def __init__(self):
        super(ChildSlither, self).__init__()
        self._slither = None

    def set_slither(self, slither):
        self._slither = slither

    @property
    def slither(self):
        return self._slither
