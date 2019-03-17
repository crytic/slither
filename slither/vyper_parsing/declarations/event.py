"""
    Event module
"""
from slither.vyper_parsing.variables.event_variable import EventVariableVyper
from slither.core.declarations.event import Event
from vyper.signatures.event_signature import EventSignature

class EventVyper(Event):
    """
    Event class
    """

    def __init__(self, event_sig, contract):
        self._name = event_sig.name
        self._event_sig = event_sig
        self._contract = contract
        self._slither = contract.slither

    @classmethod
    def from_declaration(cls, code, global_ctx, contract):
        sig = EventSignature.from_declaration(code, global_ctx)
        return cls(sig, contract)

    def analyze(self):
        # print(vars(self._event_sig))
        for index, event_arg in enumerate(self._event_sig.args):
            #  self._event_sig.indexed_list[index]
            elem = EventVariableVyper(event_arg)
            elem.analyze()
        #     self._elems.append(elem)
        #
        # self._elemsNotParsed = []
