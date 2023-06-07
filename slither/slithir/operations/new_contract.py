from typing import Optional, Any, List, Union

from slither.core.declarations import Function
from slither.core.declarations.contract import Contract
from slither.core.variables import Variable
from slither.slithir.operations import Call, OperationWithLValue
from slither.slithir.utils.utils import is_valid_lvalue
from slither.slithir.variables.constant import Constant
from slither.slithir.variables.temporary import TemporaryVariable
from slither.slithir.variables.temporary_ssa import TemporaryVariableSSA


class NewContract(Call, OperationWithLValue):  # pylint: disable=too-many-instance-attributes
    def __init__(
        self,
        contract_name: Constant,
        lvalue: Union[TemporaryVariableSSA, TemporaryVariable],
        names: Optional[List[str]] = None,
    ) -> None:
        """
        #### Parameters
        names -
            For calls of the form f({argName1 : arg1, ...}), the names of parameters listed in call order.
            Otherwise, None.
        """
        assert isinstance(contract_name, Constant)
        assert is_valid_lvalue(lvalue)
        super().__init__(names=names)
        self._contract_name = contract_name
        # todo create analyze to add the contract instance
        self._lvalue = lvalue
        self._callid = None  # only used if gas/value != 0
        self._call_value = None
        self._call_salt = None

    @property
    def call_value(self):
        return self._call_value

    @call_value.setter
    def call_value(self, v):
        self._call_value = v

    @property
    def call_id(self):
        return self._callid

    @call_id.setter
    def call_id(self, c):
        self._callid = c

    @property
    def call_salt(self):
        return self._call_salt

    @call_salt.setter
    def call_salt(self, s):
        self._call_salt = s

    @property
    def contract_name(self) -> Constant:
        return self._contract_name

    @property
    def read(self) -> List[Any]:
        all_read = [self.call_salt, self.call_value] + self._unroll(self.arguments)
        # remove None
        return [x for x in all_read if x]

    @property
    def contract_created(self) -> Contract:
        contract_name = self.contract_name
        contract_instance = self.node.file_scope.get_contract_from_name(contract_name)
        assert contract_instance
        return contract_instance

    ###################################################################################
    ###################################################################################
    # region Analyses
    ###################################################################################
    ###################################################################################

    def can_reenter(self, callstack: Optional[List[Union[Function, Variable]]] = None) -> bool:
        """
        Must be called after slithIR analysis pass
        For Solidity > 0.5, filter access to public variables and constant/pure/view
        For call to this. check if the destination can re-enter
        :param callstack: check for recursion
        :return: bool
        """
        callstack = [] if callstack is None else callstack
        constructor = self.contract_created.constructor
        if constructor is None:
            return False
        if constructor in callstack:
            return False
        callstack = callstack + [constructor]
        return constructor.can_reenter(callstack)

    def can_send_eth(self) -> bool:
        """
        Must be called after slithIR analysis pass
        :return: bool
        """
        return self._call_value is not None

    # endregion

    def __str__(self) -> str:
        options = ""
        if self.call_value:
            options = f"value:{self.call_value} "
        if self.call_salt:
            options += f"salt:{self.call_salt} "
        args = [str(a) for a in self.arguments]
        lvalue = self.lvalue
        return f"{lvalue}({lvalue.type}) = new {self.contract_name}({','.join(args)}) {options}"
