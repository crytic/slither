from slither.slithir.operations.lvalue import OperationWithLValue


class TmpNewStructure(OperationWithLValue):
    def __init__(self, contract_name, lvalue):
        super().__init__()
        self._contract_name = contract_name
        self._lvalue = lvalue

    @property
    def contract_name(self):
        return self._contract_name

    @property
    def read(self):
        return []

    def __str__(self):
        return "{} = tmpnew {}".format(self.lvalue, self.contract_name)
