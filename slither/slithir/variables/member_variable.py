from .reference import ReferenceVariable

class MemberVariable(ReferenceVariable):

    COUNTER = 0

    def __init__(self, node, base, member, index=None):
        super(MemberVariable, self).__init__()
        if index is None:
            self._index = MemberVariable.COUNTER
            MemberVariable.COUNTER += 1
        else:
            self._index = index

        self._node = node
        self._member = member
        self._base = base


    @property
    def index(self):
        return self._index

    @index.setter
    def index(self, idx):
        self._index = idx

    @property
    def member(self):
        return self._member

    @member.setter
    def member(self, member):
        self._member = member

    @property
    def base(self):
        return self._base

    @base.setter
    def base(self, base):
        self._base = base

    @property
    def name(self):
        return 'MEMBER_{}'.format(self.index)

    def __str__(self):
        return self.name
