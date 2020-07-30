"""
    Event module
"""
from typing import TYPE_CHECKING, List

from slither.core.declarations.event import Event
from slither.core.variables.event_variable import EventVariable
from slither.solc_parsing.types.types import EventDefinition, VariableDeclaration
from slither.solc_parsing.variables.event_variable import EventVariableSolc

if TYPE_CHECKING:
    from slither.solc_parsing.declarations.contract import ContractSolc


class EventSolc:
    """
    Event class
    """

    def __init__(self, event: Event, event_data: EventDefinition, contract_parser: "ContractSolc"):
        self._event: Event = event
        event.set_contract(contract_parser.underlying_contract)

        self._parser_contract: "ContractSolc" = contract_parser

        self._event.name = event_data.name
        self._elemsNotParsed: List[VariableDeclaration] = event_data.params.params

    def analyze(self, contract: "ContractSolc"):
        for elem_to_parse in self._elemsNotParsed:
            elem = EventVariable()
            elem.set_offset(elem_to_parse.src, self._parser_contract.slither)
            elem_parser = EventVariableSolc(elem, elem_to_parse)
            elem_parser.analyze(contract)

            self._event.elems.append(elem)

        self._elemsNotParsed = []
