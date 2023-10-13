from typing import List

from slither.core.declarations.structure import Structure
from slither.core.variables.structure_variable import StructureVariable
from slither.vyper_parsing.variables.structure_variable import StructureVariableVyper
from slither.vyper_parsing.ast.types import StructDef, AnnAssign


class StructVyper:  # pylint: disable=too-few-public-methods
    def __init__(
        self,
        st: Structure,
        struct: StructDef,
    ) -> None:

        self._structure = st
        st.name = struct.name
        st.canonical_name = struct.name + self._structure.contract.name

        self._elemsNotParsed: List[AnnAssign] = struct.body

    def analyze(self, contract) -> None:
        for elem_to_parse in self._elemsNotParsed:
            elem = StructureVariable()
            elem.set_structure(self._structure)
            elem.set_offset(elem_to_parse.src, self._structure.contract.compilation_unit)

            elem_parser = StructureVariableVyper(elem, elem_to_parse)
            elem_parser.analyze(contract)

            self._structure.elems[elem.name] = elem
            self._structure.add_elem_in_order(elem.name)
        self._elemsNotParsed = []
