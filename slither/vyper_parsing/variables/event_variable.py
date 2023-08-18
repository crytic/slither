from typing import Dict

from slither.core.variables.event_variable import EventVariable
from slither.vyper_parsing.type_parsing import parse_type
from slither.vyper_parsing.ast.types import AnnAssign


class EventVariableVyper:
    def __init__(self, variable: EventVariable, variable_data: AnnAssign):
        print(variable_data)
        self._variable = variable
        self._variable.name = variable_data.target.id
        # TODO self._variable.indexed
        self._elem_to_parse = variable_data.annotation

    @property
    def underlying_variable(self) -> EventVariable:
        return self._variable

    def analyze(self, contract) -> None:
        self._variable.type = parse_type(self._elem_to_parse, contract)
