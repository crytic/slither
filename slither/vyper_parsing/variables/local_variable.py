from typing import Union

from slither.core.variables.local_variable import LocalVariable
from slither.vyper_parsing.ast.types import Arg, Name, AnnAssign, Subscript, Call, Tuple
from slither.vyper_parsing.type_parsing import parse_type


class LocalVariableVyper:
    def __init__(self, variable: LocalVariable, variable_data: Union[Arg, AnnAssign, Name]) -> None:
        self._variable: LocalVariable = variable

        if isinstance(variable_data, Arg):
            self._variable.name = variable_data.arg
            self._elem_to_parse = variable_data.annotation
        elif isinstance(variable_data, AnnAssign):
            self._variable.name = variable_data.target.id
            self._elem_to_parse = variable_data.annotation
        else:
            assert isinstance(variable_data, Name)
            self._variable.name = variable_data.id
            self._elem_to_parse = variable_data

        assert isinstance(self._elem_to_parse, (Name, Subscript, Call, Tuple))

        # Vyper does not have data locations or storage pointers.
        # If this was left as default, reference types would be considered storage by `LocalVariable.is_storage`
        self._variable.set_location("memory")

    @property
    def underlying_variable(self) -> LocalVariable:
        return self._variable

    def analyze(self, contract) -> None:
        self._variable.type = parse_type(self._elem_to_parse, contract)
