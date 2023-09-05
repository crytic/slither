"""
    Event module
"""

from slither.core.variables.event_variable import EventVariable
from slither.vyper_parsing.variables.event_variable import EventVariableVyper
from slither.core.declarations.event import Event
from slither.vyper_parsing.ast.types import AnnAssign, Pass


from slither.vyper_parsing.ast.types import EventDef


class EventVyper:  # pylint: disable=too-few-public-methods
    """
    Event class
    """

    def __init__(self, event: Event, event_def: EventDef) -> None:

        self._event = event
        self._event.name = event_def.name
        self._elemsNotParsed = event_def.body

    def analyze(self, contract) -> None:
        for elem_to_parse in self._elemsNotParsed:
            if not isinstance(elem_to_parse, AnnAssign):
                assert isinstance(elem_to_parse, Pass)
                continue

            elem = EventVariable()

            elem.set_offset(elem_to_parse.src, self._event.contract.compilation_unit)
            event_parser = EventVariableVyper(elem, elem_to_parse)
            event_parser.analyze(contract)

            self._event.elems.append(elem)

        self._elemsNotParsed = []
