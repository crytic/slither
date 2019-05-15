
class ChildContract:

    def __init__(self):
        super(ChildContract, self).__init__()
        self._contract = None

    def set_contract(self, contract):
        self._contract = contract

    @property
    def contract(self):
        return self._contract

