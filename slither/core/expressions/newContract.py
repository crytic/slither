from expression import Expression

class NewContract(Expression):

    def __init__(self, contract_name):
        super(NewContract, self).__init__()
        self._contract_name = contract_name

    @property
    def contract_name(self):
        return self._contract_name

    def __str__(self):
        return 'new ' + str(self._contract_name)

