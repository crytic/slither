from typing import TYPE_CHECKING, Union, List

from slither.core.declarations import SolidityVariableComposed
from slither.slithir.operations.lvalue import OperationWithLValue
from slither.slithir.utils.utils import is_valid_lvalue, is_valid_rvalue
from slither.slithir.variables.index_variable import IndexVariable

if TYPE_CHECKING:
    from slither.slithir.utils.utils import VALID_RVALUE, VALID_LVALUE
    from slither.core.solidity_types.type import Type


class Index(OperationWithLValue):
    def __init__(self,
                 result: IndexVariable,
                 left_variable: Union["VALID_LVALUE", SolidityVariableComposed],
                 right_variable: "VALID_RVALUE",
                 index_type: "Type"):
        super(Index, self).__init__()
        assert is_valid_lvalue(left_variable) or left_variable == SolidityVariableComposed(
            "msg.data"
        )
        assert is_valid_rvalue(right_variable)
        assert isinstance(result, IndexVariable)
        self._variables: List[Union["VALID_LVALUE",
                                    SolidityVariableComposed,
                                    "VALID_RVALUE"]] = [left_variable, right_variable]
        self._type: "Type" = index_type
        self._lvalue: IndexVariable = result

    @property
    def read(self) -> List[Union["VALID_LVALUE", SolidityVariableComposed, "VALID_RVALUE"]]:
        return list(self.variables)

    @property
    def variables(self) -> List[Union["VALID_LVALUE", SolidityVariableComposed, "VALID_RVALUE"]]:
        return self._variables

    @property
    def variable_left(self) -> Union["VALID_LVALUE", SolidityVariableComposed]:
        return self._variables[0]

    @property
    def variable_right(self) -> "VALID_RVALUE":
        return self._variables[1]

    @property
    def index_type(self) -> "Type":
        return self._type

    @property
    def lvalue(self) -> IndexVariable:
        return self._lvalue

    @lvalue.setter
    def lvalue(self, lvalue: IndexVariable):
        self._lvalue = lvalue

    def __str__(self):
        return "{}({}) -> {}[{}]".format(
            self.lvalue, self.lvalue.type, self.variable_left, self.variable_right
        )
