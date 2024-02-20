from slither.core.variables.state_variable import StateVariable
from slither.vyper_parsing.ast.types import VariableDecl
from slither.vyper_parsing.type_parsing import parse_type
from slither.vyper_parsing.expressions.expression_parsing import parse_expression


class StateVariableVyper:
    def __init__(self, variable: StateVariable, variable_data: VariableDecl) -> None:
        self._variable: StateVariable = variable
        self._variable.name = variable_data.target.id
        self._variable.is_constant = variable_data.is_constant
        self._variable.is_immutable = variable_data.is_immutable
        self._variable.visibility = "public" if variable_data.is_public else "internal"
        self._elem_to_parse = variable_data.annotation

        if variable_data.value is not None:
            self._variable.initialized = True
            self._initializedNotParsed = variable_data.value

    @property
    def underlying_variable(self) -> StateVariable:
        return self._variable

    def analyze(self, contract) -> None:
        self._variable.type = parse_type(self._elem_to_parse, contract)

        if self._variable.initialized:
            self._variable.expression = parse_expression(self._initializedNotParsed, contract)
            self._initializedNotParsed = None
