"""
    Event module
"""
from typing import TYPE_CHECKING, Dict, List

from slither.core.variables.event_variable import EventVariable
from slither.solc_parsing.variables.event_variable import EventVariableSolc
from slither.core.declarations.event import Event
from slither.solc_parsing.types.types import EventDefinition, VariableDeclaration

if TYPE_CHECKING:
    from slither.solc_parsing.declarations.contract import ContractSolc


class EventSolc:
    """
    Event class
    """

    def __init__(self, event: Event, event_data: EventDefinition, contract_parser: "ContractSolc"):

        self._event = event
        event.set_contract(contract_parser.underlying_contract)
        self._parser_contract = contract_parser

        self._parser_contract: "ContractSolc" = contract_parser

        self._event.name = event_data.name
        self._elemsNotParsed: List[VariableDeclaration] = event_data.params.params

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
