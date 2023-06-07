from typing import Any, Union, Tuple, List, Optional
from slither.core.declarations import Modifier
from slither.core.declarations.function import Function
from slither.core.declarations.function_contract import FunctionContract
from slither.slithir.operations.call import Call
from slither.slithir.operations.lvalue import OperationWithLValue
from slither.slithir.variables.constant import Constant
from slither.slithir.variables.temporary import TemporaryVariable
from slither.slithir.variables.temporary_ssa import TemporaryVariableSSA
from slither.slithir.variables.tuple import TupleVariable
from slither.slithir.variables.tuple_ssa import TupleVariableSSA


class InternalCall(Call, OperationWithLValue):  # pylint: disable=too-many-instance-attributes
    def __init__(
        self,
        function: Union[Function, Tuple[str, str]],
        nbr_arguments: int,
        result: Optional[
            Union[TupleVariableSSA, TemporaryVariableSSA, TupleVariable, TemporaryVariable]
        ],
        type_call: str,
        names: Optional[List[str]] = None,
    ) -> None:
        # pylint: disable=too-many-arguments
        """
        #### Parameters
        names -
            For calls of the form f({argName1 : arg1, ...}), the names of parameters listed in call order.
            Otherwise, None.
        """
        super().__init__(names=names)
        self._contract_name = ""
        if isinstance(function, Function):
            self._function: Optional[Function] = function
            self._function_name = function.name
            if isinstance(function, FunctionContract):
                self._contract_name = function.contract_declarer.name
        else:
            self._function = None
            self._function_name, self._contract_name = function
        # self._contract = contract
        self._nbr_arguments = nbr_arguments
        self._type_call = type_call
        self._lvalue = result
        # function_candidates is only used as an helper to retrieve the "function" object
        # For top level function called through a import renamed
        # See SolidityImportPlaceHolder usages
        self.function_candidates: Optional[List[Function]] = None

    @property
    def read(self) -> List[Any]:
        return list(self._unroll(self.arguments))

    @property
    def function(self) -> Optional[Function]:
        return self._function

    @function.setter
    def function(self, f):
        self._function = f

    @property
    def function_name(self) -> Constant:
        return self._function_name

    @property
    def contract_name(self) -> str:
        return self._contract_name

    @property
    def nbr_arguments(self) -> int:
        return self._nbr_arguments

    @property
    def type_call(self) -> str:
        return self._type_call

    @property
    def is_modifier_call(self):
        """
        Check if the destination is a modifier
        :return: bool
        """
        return isinstance(self.function, Modifier)

    def __str__(self):
        args = [str(a) for a in self.arguments]
        if not self.lvalue:
            lvalue = ""
        elif isinstance(self.lvalue.type, (list,)):
            lvalue = f"{self.lvalue}({','.join(str(x) for x in self.lvalue.type)}) = "
        else:
            lvalue = f"{self.lvalue}({self.lvalue.type}) = "
        if self.is_modifier_call:
            txt = "{}MODIFIER_CALL, {}({})"
        else:
            txt = "{}INTERNAL_CALL, {}({})"
        return txt.format(lvalue, self.function.canonical_name, ",".join(args))
