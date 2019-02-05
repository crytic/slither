from slither.core.solidity_types.type import Type

class MappingType(Type):

    def __init__(self, type_from, type_to):
        assert isinstance(type_from, Type)
        assert isinstance(type_to, Type)
        super(MappingType, self).__init__()
        self._from = type_from
        self._to = type_to

    @property
    def type_from(self):
        return self._from

    @property
    def type_to(self):
        return self._to

    def __str__(self):
        return 'mapping({} => {})'.format(str(self._from), str(self._to))

    def __eq__(self, other):
        if not isinstance(other, MappingType):
            return False
        return self.type_from == other.type_from and self.type_to == other.type_to

    def __hash__(self):
        return hash(str(self))

