"""
    Structure module
"""
from slither.solc_parsing.variables.structure_variable import StructureVariableSolc
from slither.core.declarations.structure import Structure

class StructureSolc(Structure):
    """
    Structure class
    """
    # elems = [(type, name)]


    def __init__(self, name, canonicalName, elems):
        super(StructureSolc, self).__init__()
        self._name = name
        self._canonical_name = canonicalName
        self._elems = {}
        self._elems_ordered = []

        self._elemsNotParsed = elems

    def analyze(self):
        for elem_to_parse in self._elemsNotParsed:
            elem = StructureVariableSolc(elem_to_parse)
            elem.set_structure(self)
            elem.set_offset(elem_to_parse['src'], self.contract.slither)

            elem.analyze(self.contract)

            self._elems[elem.name] = elem
            self._elems_ordered.append(elem.name)
        self._elemsNotParsed = []

