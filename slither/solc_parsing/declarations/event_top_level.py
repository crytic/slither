"""
    EventTopLevel module
"""
from typing import TYPE_CHECKING, Dict

from slither.core.declarations.event_top_level import EventTopLevel
from slither.core.variables.event_variable import EventVariable
from slither.core.compilation_unit import SlitherCompilationUnit
from slither.solc_parsing.variables.event_variable import EventVariableSolc
from slither.solc_parsing.declarations.caller_context import CallerContextExpression

if TYPE_CHECKING:
    from slither.solc_parsing.slither_compilation_unit_solc import SlitherCompilationUnitSolc


class EventTopLevelSolc(CallerContextExpression):
    """
    EventTopLevel class
    """

    def __init__(
        self, event: EventTopLevel, event_data: Dict, slither_parser: "SlitherCompilationUnitSolc"
    ) -> None:

        self._event = event
        self._slither_parser = slither_parser

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

    def analyze(self) -> None:
        for elem_to_parse in self._elemsNotParsed:
            elem = EventVariable()
            # Todo: check if the source offset is always here
            if "src" in elem_to_parse:
                elem.set_offset(elem_to_parse["src"], self._slither_parser.compilation_unit)
            elem_parser = EventVariableSolc(elem, elem_to_parse)
            elem_parser.analyze(self)

            self._event.elems.append(elem)

        self._elemsNotParsed = []

    @property
    def is_compact_ast(self) -> bool:
        return self._slither_parser.is_compact_ast

    @property
    def compilation_unit(self) -> SlitherCompilationUnit:
        return self._slither_parser.compilation_unit

    def get_key(self) -> str:
        return self._slither_parser.get_key()

    @property
    def slither_parser(self) -> "SlitherCompilationUnitSolc":
        return self._slither_parser

    @property
    def underlying_event(self) -> EventTopLevel:
        return self._event
