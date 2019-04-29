
class ChildInheritance:

    def __init__(self):
        super(ChildInheritance, self).__init__()
        self._contract_declarer = None

    def set_contract_declarer(self, contract):
        self._contract_declarer = contract

    @property
    def contract_declarer(self):
        return self._contract_declarer
