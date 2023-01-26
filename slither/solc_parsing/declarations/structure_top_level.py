"""
    Structure module
"""
from typing import TYPE_CHECKING, Dict

from slither.core.compilation_unit import SlitherCompilationUnit
from slither.core.declarations.structure_top_level import StructureTopLevel
from slither.core.variables.structure_variable import StructureVariable
from slither.solc_parsing.declarations.caller_context import CallerContextExpression
from slither.solc_parsing.variables.structure_variable import StructureVariableSolc
from slither.solc_parsing.ast.types import StructDefinition

if TYPE_CHECKING:
    from slither.solc_parsing.slither_compilation_unit_solc import SlitherCompilationUnitSolc


class StructureTopLevelSolc(CallerContextExpression):  # pylint: disable=too-few-public-methods
    """
    Structure class
    """

    # elems = [(type, name)]

    def __init__(  # pylint: disable=too-many-arguments
        self,
        st: StructureTopLevel,
        struct_def: StructDefinition,
        slither_parser: "SlitherCompilationUnitSolc",
    ):
        self._structure = st
        st.name = struct_def.name
        if struct_def.canonical_name:
            st.canonical_name = struct_def.canonical_name
        else:
            st.canonical_name = struct_def.name
        self._slither_parser = slither_parser

        self._elemsNotParsed = struct_def.members

    def analyze(self):
        for elem_to_parse in self._elemsNotParsed:
            elem = StructureVariable()
            elem.set_structure(self._structure)
            elem.set_offset(elem_to_parse.src, self._slither_parser.compilation_unit)

            elem_parser = StructureVariableSolc(elem, elem_to_parse)
            elem_parser.analyze(self)

            self._structure.elems[elem.name] = elem
            self._structure.add_elem_in_order(elem.name)
        self._elemsNotParsed = []

    @property
    def compilation_unit(self) -> SlitherCompilationUnit:
        return self._slither_parser.compilation_unit

    @property
    def slither_parser(self) -> "SlitherCompilationUnitSolc":
        return self._slither_parser

    @property
    def underlying_structure(self) -> StructureTopLevel:
        return self._structure
