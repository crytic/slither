"""
    Event module
"""
from typing import TYPE_CHECKING, Dict

from slither.solc_parsing.variables.event_variable import EventVariableSolc
from slither.core.declarations.event import Event

if TYPE_CHECKING:
    from slither.core.declarations import Contract


class EventSolc(Event):
    """
    Event class
    """

    def __init__(self, event: Dict, contract: "Contract"):
        super(EventSolc, self).__init__()
        self._contract = contract

        self._elems = []
        if self.is_compact_ast:
            self._name = event["name"]
            elems = event["parameters"]
            assert elems["nodeType"] == "ParameterList"
            self._elemsNotParsed = elems["parameters"]
        else:
            self._name = event["attributes"]["name"]
            elems = event["children"][0]

            assert elems["name"] == "ParameterList"
            if "children" in elems:
                self._elemsNotParsed = elems["children"]
            else:
                self._elemsNotParsed = []

    @property
    def is_compact_ast(self) -> bool:
        return self.contract.is_compact_ast

    def analyze(self, contract: "Contract"):
        for elem_to_parse in self._elemsNotParsed:
            elem = EventVariableSolc(elem_to_parse)
            elem.analyze(contract)
            self._elems.append(elem)

        self._elemsNotParsed = []
