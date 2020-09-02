from typing import Optional, List

from slither.core.expressions.expression import Expression


class CallExpression(Expression):  # pylint: disable=too-many-instance-attributes
    def __init__(self, called, arguments, type_call):
        assert isinstance(called, Expression)
        super(CallExpression, self).__init__()
        self._called: Expression = called
        self._arguments: List[Expression] = arguments
        self._type_call: str = type_call
        # gas and value are only available if the syntax is {gas: , value: }
        # For the .gas().value(), the member are considered as function call
        # And converted later to the correct info (convert.py)
        self._gas: Optional[Expression] = None
        self._value: Optional[Expression] = None
        self._salt: Optional[Expression] = None

    @property
    def call_value(self) -> Optional[Expression]:
        return self._value

    @call_value.setter
    def call_value(self, v):
        self._value = v

    @property
    def call_gas(self) -> Optional[Expression]:
        return self._gas

    @call_gas.setter
    def call_gas(self, gas):
        self._gas = gas

    @property
    def call_salt(self):
        return self._salt

    @call_salt.setter
    def call_salt(self, salt):
        self._salt = salt

    @property
    def called(self) -> Expression:
        return self._called

    @property
    def arguments(self) -> List[Expression]:
        return self._arguments

    @property
    def type_call(self) -> str:
        return self._type_call

    def __str__(self):
        txt = str(self._called)
        if self.call_gas or self.call_value:
            gas = f"gas: {self.call_gas}" if self.call_gas else ""
            value = f"value: {self.call_value}" if self.call_value else ""
            salt = f"salt: {self.call_salt}" if self.call_salt else ""
            if gas or value or salt:
                options = [gas, value, salt]
                txt += "{" + ",".join([o for o in options if o != ""]) + "}"
        return txt + "(" + ",".join([str(a) for a in self._arguments]) + ")"
