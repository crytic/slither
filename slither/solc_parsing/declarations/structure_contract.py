"""
    Structure module
"""
from typing import List, TYPE_CHECKING, Dict

from slither.core.variables.structure_variable import StructureVariable
from slither.solc_parsing.variables.structure_variable import StructureVariableSolc
from slither.core.declarations.structure import Structure

if TYPE_CHECKING:
    from slither.solc_parsing.declarations.contract import ContractSolc


class StructureContractSolc:  # pylint: disable=too-few-public-methods
    """
    Structure class
    """

    # elems = [(type, name)]

    def __init__(  # pylint: disable=too-many-arguments
        self, st: Structure, struct: Dict, contract_parser: "ContractSolc",
    ):

        if contract_parser.is_compact_ast:
            name = struct["name"]
            attributes = struct
        else:
            name = struct["attributes"][contract_parser.get_key()]
            attributes = struct["attributes"]
        if "canonicalName" in attributes:
            canonicalName = attributes["canonicalName"]
        else:
            canonicalName = contract_parser.underlying_contract.name + "." + name

        children = struct["members"] if "members" in struct else struct.get("children", [])

        self._structure = st
        st.name = name
        st.canonical_name = canonicalName
        self._contract_parser = contract_parser

        self._elemsNotParsed = children

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
