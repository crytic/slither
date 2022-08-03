"""
    Event module
"""
from typing import TYPE_CHECKING, Dict

from slither.core.variables.event_variable import EventVariable
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
            for elem in event_data["children"]:
                # From Solidity 0.6.3 to 0.6.10 (included)
                # Comment above a event might be added in the children
                # of an event for the legacy ast
                if elem["name"] == "ParameterList":
                    if "children" in elem:
                        self._elemsNotParsed = elem["children"]
                    else:
                        self._elemsNotParsed = []

    @property
    def is_compact_ast(self) -> bool:
        return self._parser_contract.is_compact_ast

    def analyze(self, contract: "ContractSolc"):
        for elem_to_parse in self._elemsNotParsed:
            elem = EventVariable()
            # Todo: check if the source offset is always here
            if "src" in elem_to_parse:
                elem.set_offset(
                    elem_to_parse["src"], self._parser_contract.underlying_contract.compilation_unit
                )
            elem_parser = EventVariableSolc(elem, elem_to_parse)
            elem_parser.analyze(contract)

            self._event.elems.append(elem)

        self._elemsNotParsed = []
