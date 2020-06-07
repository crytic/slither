from .expression import Expression

class NewContract(Expression):

    def __init__(self, contract_name):
        super(NewContract, self).__init__()
        self._contract_name = contract_name
        self._gas = None
        self._value = None
        self._salt = None


    @property
    def contract_name(self):
        return self._contract_name

    @property
    def call_value(self):
        return self._value

    @call_value.setter
    def call_value(self, v):
        self._value = v

    @property
    def call_salt(self):
        return self._salt

    @call_salt.setter
    def call_salt(self, salt):
        self._salt = salt


    def __str__(self):
        return 'new ' + str(self._contract_name)

