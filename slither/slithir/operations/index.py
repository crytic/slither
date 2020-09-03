from slither.core.declarations import SolidityVariableComposed
from slither.slithir.operations.lvalue import OperationWithLValue
from slither.slithir.utils.utils import is_valid_lvalue, is_valid_rvalue
from slither.slithir.variables.reference import ReferenceVariable


class Index(OperationWithLValue):
    def __init__(self, result, left_variable, right_variable, index_type):
        super().__init__()
        assert is_valid_lvalue(left_variable) or left_variable == SolidityVariableComposed(
            "msg.data"
        )
        assert is_valid_rvalue(right_variable)
        assert isinstance(result, ReferenceVariable)
        self._variables = [left_variable, right_variable]
        self._type = index_type
        self._lvalue = result

    @property
    def read(self):
        return list(self.variables)

    @property
    def variables(self):
        return self._variables

    @property
    def variable_left(self):
        return self._variables[0]

    @property
    def variable_right(self):
        return self._variables[1]

    @property
    def index_type(self):
        return self._type

    def __str__(self):
        return "{}({}) -> {}[{}]".format(
            self.lvalue, self.lvalue.type, self.variable_left, self.variable_right
        )
