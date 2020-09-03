"""
    Structure module
"""
from typing import List, TYPE_CHECKING

from slither.core.variables.structure_variable import StructureVariable
from slither.solc_parsing.variables.structure_variable import StructureVariableSolc
from slither.core.declarations.structure import Structure

if TYPE_CHECKING:
    from slither.solc_parsing.declarations.contract import ContractSolc


class StructureSolc:  # pylint: disable=too-few-public-methods
    """
    Structure class
    """

    # elems = [(type, name)]

    def __init__(  # pylint: disable=too-many-arguments
        self,
        st: Structure,
        name: str,
        canonicalName: str,
        elems: List[str],
        contract_parser: "ContractSolc",
    ):
        self._structure = st
        st.name = name
        st.canonical_name = canonicalName
        self._contract_parser = contract_parser

        self._elemsNotParsed = elems

    def analyze(self):
        for elem_to_parse in self._elemsNotParsed:
            elem = StructureVariable()
            elem.set_structure(self._structure)
            elem.set_offset(elem_to_parse["src"], self._structure.contract.slither)

            elem_parser = StructureVariableSolc(elem, elem_to_parse)
            elem_parser.analyze(self._contract_parser)

            self._structure.elems[elem.name] = elem
            self._structure.add_elem_in_order(elem.name)
        self._elemsNotParsed = []
