
class ChildStructure(object):

    def __init__(self):
        super(ChildStructure, self).__init__()
        self._structure = None

    def set_structure(self, structure):
        self._structure = structure

    @property
    def structure(self):
        return self._structure
