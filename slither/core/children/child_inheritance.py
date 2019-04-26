
class ChildInheritance:

    def __init__(self):
        super(ChildInheritance, self).__init__()
        self._original_contract = None

    def set_original_contract(self, original_contract):
        self._original_contract = original_contract

    @property
    def original_contract(self):
        return self._original_contract
