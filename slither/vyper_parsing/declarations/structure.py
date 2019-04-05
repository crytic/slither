"""
    Structure module
"""
from slither.vyper_parsing.variables.structure_variable import StructureVariableVyper
from slither.core.declarations.structure import Structure

class StructureVyper(Structure):
    """
    Structure class
    """
    # elems = [(type, name)]


    def __init__(self, name, ast_struct, code):
        super().__init__()
        self._name = name
        # self._canonical_name = canonicalName
        self._elems = {}
        self._ast_struct = ast_struct
        self._code = code
        self._elemsNotParsed = code

    def analyze(self):
        for elem_tuple in self._code:
            print(vars(elem_tuple[1]))
            # elem = StructureVariableVyper(elem_tuple)
            # elem.set_structure(self)
            # elem.set_offset(elem_to_parse['src'], self.contract.slither)
            #
            # elem.analyze(self.contract)
            #
            # self._elems[elem.name] = elem
        self._elemsNotParsed = []
