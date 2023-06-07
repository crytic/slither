from typing import Any, Optional, List

from slither.core.expressions.expression import Expression


class CallExpression(Expression):  # pylint: disable=too-many-instance-attributes
    def __init__(
        self,
        called: Expression,
        arguments: List[Any],
        type_call: str,
        names: Optional[List[str]] = None,
    ) -> None:
        """
        #### Parameters
        called -
            The expression denoting the function to be called
        arguments -
            List of argument expressions
        type_call -
            A string formatting of the called function's return type
        names -
            For calls with named fields, list fields in call order.
            For calls without named fields, None.
        """
        assert isinstance(called, Expression)
        assert (names is None) or isinstance(names, list)
        super().__init__()
        self._called: Expression = called
        self._arguments: List[Expression] = arguments
        self._type_call: str = type_call
        self._names: Optional[List[str]] = names
        # gas and value are only available if the syntax is {gas: , value: }
        # For the .gas().value(), the member are considered as function call
        # And converted later to the correct info (convert.py)
        self._gas: Optional[Expression] = None
        self._value: Optional[Expression] = None
        self._salt: Optional[Expression] = None

    @property
    def names(self) -> Optional[List[str]]:
        """
        For calls with named fields, list fields in call order.
        For calls without named fields, None.
        """
        return self._names

    @property
    def call_value(self) -> Optional[Expression]:
        return self._value

    @call_value.setter
    def call_value(self, v: Optional[Expression]) -> None:
        self._value = v

    @property
    def call_gas(self) -> Optional[Expression]:
        return self._gas

    @call_gas.setter
    def call_gas(self, gas: Optional[Expression]) -> None:
        self._gas = gas

    @property
    def call_salt(self) -> Optional[Expression]:
        return self._salt

    @call_salt.setter
    def call_salt(self, salt: Optional[Expression]) -> None:
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

    def __str__(self) -> str:
        txt = str(self._called)
        if self.call_gas or self.call_value:
            gas = f"gas: {self.call_gas}" if self.call_gas else ""
            value = f"value: {self.call_value}" if self.call_value else ""
            salt = f"salt: {self.call_salt}" if self.call_salt else ""
            if gas or value or salt:
                options = [gas, value, salt]
                txt += "{" + ",".join([o for o in options if o != ""]) + "}"
        args = (
            "{" + ",".join([f"{n}:{str(a)}" for (a, n) in zip(self._arguments, self._names)]) + "}"
            if self._names is not None
            else ",".join([str(a) for a in self._arguments])
        )
        return txt + "(" + args + ")"
