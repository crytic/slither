"""
    Structure module
"""
from typing import TYPE_CHECKING, Dict, List

from slither.core.declarations.structure import Structure
from slither.core.variables.structure_variable import StructureVariable
from slither.solc_parsing.variables.structure_variable import StructureVariableSolc
from slither.solc_parsing.ast.types import VariableDeclaration, StructDefinition

if TYPE_CHECKING:
    from slither.solc_parsing.declarations.contract import ContractSolc


class StructureContractSolc:  # pylint: disable=too-few-public-methods
    """
    Structure class
    """

    # elems = [(type, name)]

    def __init__(  # pylint: disable=too-many-arguments
        self,
        st: Structure,
        struct_def: StructDefinition,
        contract_parser: "ContractSolc",
    ) -> None:

        self._structure = st
        st.name = struct_def.name
        if struct_def.canonical_name:
            st.canonical_name = struct_def.canonical_name
        else:
            st.canonical_name = contract_parser.underlying_contract.name + "." + struct_def.name
        self._contract_parser = contract_parser

        self._elemsNotParsed: List[VariableDeclaration] = struct_def.members

    def analyze(self) -> None:
        for elem_to_parse in self._elemsNotParsed:
            elem = StructureVariable()
            elem.set_structure(self._structure)
            elem.set_offset(elem_to_parse.src, self._structure.contract.compilation_unit)

            elem_parser = StructureVariableSolc(elem, elem_to_parse)
            elem_parser.analyze(self._contract_parser)

            self._structure.elems[elem.name] = elem
            self._structure.add_elem_in_order(elem.name)
        self._elemsNotParsed = []
