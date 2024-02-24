from slither.slithir.operations import HighLevelCall, Operation
from slither.core.declarations import Function
from slither.slithir.operations import (
    Binary,
    BinaryType,
)
from slither.detectors.oracles.supported_oracles.help_functions import check_revert, return_boolean
from slither.slithir.variables.constant import Constant

# This class was created to store variable and all conditional nodes where it is used
class VarInCondition:  # pylint: disable=too-few-public-methods
    def __init__(self, _var, _nodes):
        self.var = _var
        self.nodes_with_var = _nodes


class Oracle:  # pylint: disable=too-few-public-methods, too-many-instance-attributes
    def __init__(self, _calls):
        self.calls = _calls
        self.contract = None
        self.function = None
        self.node = None
        self.oracle_vars = []
        # self.vars_in_condition = []
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

    def set_function(self, _function):
        self.function = _function

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
    

    # Data validation functions
    def naive_data_validation(self):
        return self

    @staticmethod
    def check_greater_zero(ir: Operation) -> bool:
        if isinstance(ir.variable_right, Constant):
            if ir.type is (BinaryType.GREATER) or ir.type is (BinaryType.NOT_EQUAL):
                if ir.variable_right.value == 0:
                    return True
        elif isinstance(ir.variable_left, Constant):
            if ir.type is (BinaryType.LESS) or ir.type is (BinaryType.NOT_EQUAL):
                if ir.variable_left.value == 0:
                    return True
        return False

    @staticmethod
    def timestamp_in_node(node) -> bool:
        if "block.timestamp" in str(node):
            return True
        return False

    # This function checks if the timestamp value is validated.
    def check_staleness(self, var: VarInCondition) -> bool:
        if var is None:
            return False
        for node in var.nodes_with_var:
            # This is temporarily check which will be improved in the future. Mostly we are looking for block.timestamp and trust the developer that he is using it correctly
            if self.timestamp_in_node(node):
                return True

        return False

    # This functions validates checks of price value
    def check_price(self, var: VarInCondition) -> bool:
        if var is None:
            return False
        for node in var.nodes_with_var:
            for ir in node.irs:
                if isinstance(ir, Binary):
                    if self.check_greater_zero(ir):
                        return True
                    # If the conditions does not match we are looking for revert or return node
                    return check_revert(node) or return_boolean(node)

        return False
