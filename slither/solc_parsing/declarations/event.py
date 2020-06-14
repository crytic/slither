"""
    Event module
"""
from typing import TYPE_CHECKING, Dict

from slither.solc_parsing.variables.event_variable import EventVariableSolc
from slither.core.declarations.event import Event

if TYPE_CHECKING:
    from slither.solc_parsing.declarations.contract import ContractSolc


class EventSolc:
    """
    Event class
    """

    def __init__(self, event: Event, event_data: Dict, contract_parser: "ContractSolc"):

        self._event = event
        event.set_contract(contract_parser.underlying_contract)
        self._parser_contract = contract_parser

        if self.is_compact_ast:
            self._event.name = event_data["name"]
            elems = event_data["parameters"]
            assert elems["nodeType"] == "ParameterList"
            self._elemsNotParsed = elems["parameters"]
        else:
            self._event.name = event_data["attributes"]["name"]
            elems = event_data["children"][0]

            assert elems["name"] == "ParameterList"
            if "children" in elems:
                self._elemsNotParsed = elems["children"]
            else:
                self._elemsNotParsed = []

    @property
    def is_compact_ast(self) -> bool:
        return self._parser_contract.is_compact_ast

    def analyze(self, contract: "ContractSolc"):
        for elem_to_parse in self._elemsNotParsed:
            elem = EventVariableSolc(elem_to_parse)
            elem.analyze(contract)
            self._event.elems.append(elem)

        self._elemsNotParsed = []
