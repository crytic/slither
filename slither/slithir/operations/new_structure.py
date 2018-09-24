from slither.slithir.operations.call import Call
from slither.slithir.operations.lvalue import OperationWithLValue

from slither.slithir.utils.utils import is_valid_lvalue

from slither.core.declarations.structure import Structure

class NewStructure(Call, OperationWithLValue):

    def __init__(self, structure_name, lvalue):
        super(NewStructure, self).__init__()
        assert isinstance(structure_name, Structure)
        assert is_valid_lvalue(lvalue)
        self._structure_name = structure_name
        # todo create analyze to add the contract instance
        self._lvalue = lvalue

    @property
    def read(self):
        return list(self.arguments)

    @property
    def structure_name(self):
        return self._structure_name

    def __str__(self):
        args = [str(a) for a in self.arguments]
        return '{} = new {}({})'.format(self.lvalue, self.structure_name, ','.join(args))
