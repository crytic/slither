from slither.slithir.operations import HighLevelCall, Operation
from slither.core.declarations import Function

# This class was created to store variable and all conditional nodes where it is used
class VarInCondition:
    def __init__(self, _var, _nodes):
        self.var = _var
        self.nodes_with_var = _nodes


class Oracle:  # pylint: disable=too-few-public-methods
    def __init__(self, _calls):
        self.calls = _calls
        self.contract = None
        self.function = None
        self.node = None
        self.oracle_vars = []
        self.vars_in_condition = []
        self.vars_not_in_condition = []
        self.returned_vars_indexes = None
        self.interface = None
        self.oracle_api = None
        self.oracle_type = None

    def get_calls(self):
        return self.calls

    def is_instance_of(self, ir: Operation) -> bool:
        return isinstance(ir, HighLevelCall) and (
            isinstance(ir.function, Function) and self.compare_call(ir.function.name)
        )

    def set_node(self, _node):
        self.node = _node

    def compare_call(self, function) -> bool:
        for call in self.calls:
            if call in str(function):
                return True
        return False

    def set_data(self, _contract, _function, _returned_vars_indexes, _interface, _oracle_api):
        self.contract = _contract
        self.function = _function
        self.returned_vars_indexes = _returned_vars_indexes
        self.interface = _interface
        self.oracle_api = _oracle_api

    # Data validation helpful functions
    def naive_data_validation(self):
        return []

    def check_price(self, var: VarInCondition) -> bool:
        if var is None:
            return False
        return True

    def check_staleness(self, var: VarInCondition) -> bool:
        if var is None:
            return False
        return True
