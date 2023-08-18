import logging
import re
from typing import Dict, Optional, Union


from slither.core.variables.variable import Variable
from slither.core.solidity_types.elementary_type import (
    ElementaryType,
    NonElementaryType,
)
from slither.solc_parsing.exceptions import ParsingError

from slither.vyper_parsing.ast.types import VariableDecl, Name, Subscript, ASTNode, Call, Arg
from slither.vyper_parsing.type_parsing import parse_type


class VariableDeclarationVyper:
    # pylint: disable=too-many-branches
    def __init__(self, variable: Variable, variable_data: VariableDecl) -> None:
        """
        A variable can be declared through a statement, or directly.
        If it is through a statement, the following children may contain
        the init value.
        It may be possible that the variable is declared through a statement,
        but the init value is declared at the VariableDeclaration children level
        """

        self._variable = variable
        if isinstance(variable_data, Arg):
            self._variable.name = variable_data.arg
        else:
            self._variable.name = variable_data.target.id
        self._was_analyzed: bool = False
        self._initializedNotParsed: Optional[ASTNode] = None

        if isinstance(variable_data.annotation, Subscript):
            self._elem_to_parse = variable_data.annotation.value.id
        elif isinstance(variable_data.annotation, Name):
            self._elem_to_parse = variable_data.annotation.id
        else:  # Event defs with indexed args
            assert isinstance(variable_data.annotation, Call)
            self._elem_to_parse = variable_data.annotation.args[0].id
        self._init_from_declaration(variable_data)
        # self._elem_to_parse: Optional[Union[Dict, UnknownType]] = None
        # self._initializedNotParsed: Optional[Dict] = None

        # self._is_compact_ast = False

        # self._reference_id: Optional[int] = None

    @property
    def underlying_variable(self) -> Variable:
        return self._variable

    def _init_from_declaration(self, var: VariableDecl):
        # Only state variables

        pass

    #     self._handle_comment(attributes)
    # Args do not have intial value
    # print(var.value)
    # assert var.value is None
    # def _init_from_declaration(
    #     self, var: Dict, init: Optional[Dict]
    # ) -> None:  # pylint: disable=too-many-branches
    #     if self._is_compact_ast:
    #         attributes = var
    #         self._typeName = attributes["typeDescriptions"]["typeString"]
    #     else:
    #         assert len(var["children"]) <= 2
    #         assert var["name"] == "VariableDeclaration"

    #         attributes = var["attributes"]
    #         self._typeName = attributes["type"]

    #     self._variable.name = attributes["name"]
    #     # self._arrayDepth = 0
    #     # self._isMapping = False
    #     # self._mappingFrom = None
    #     # self._mappingTo = False
    #     # self._initial_expression = None
    #     # self._type = None

    #     # Only for comapct ast format
    #     # the id can be used later if referencedDeclaration
    #     # is provided
    #     if "id" in var:
    #         self._reference_id = var["id"]

    #     if "constant" in attributes:
    #         self._variable.is_constant = attributes["constant"]

    #     if "mutability" in attributes:
    #         # Note: this checked is not needed if "constant" was already in attribute, but we keep it
    #         # for completion
    #         if attributes["mutability"] == "constant":
    #             self._variable.is_constant = True
    #         if attributes["mutability"] == "immutable":
    #             self._variable.is_immutable = True

    #     self._analyze_variable_attributes(attributes)

    #     if self._is_compact_ast:
    #         if var["typeName"]:
    #             self._elem_to_parse = var["typeName"]
    #         else:
    #             self._elem_to_parse = UnknownType(var["typeDescriptions"]["typeString"])
    #     else:
    #         if not var["children"]:
    #             # It happens on variable declared inside loop declaration
    #             try:
    #                 self._variable.type = ElementaryType(self._typeName)
    #                 self._elem_to_parse = None
    #             except NonElementaryType:
    #                 self._elem_to_parse = UnknownType(self._typeName)
    #         else:
    #             self._elem_to_parse = var["children"][0]

    #     if self._is_compact_ast:
    #         self._initializedNotParsed = init
    #         if init:
    #             self._variable.initialized = True
    #     else:
    #         if init:  # there are two way to init a var local in the AST
    #             assert len(var["children"]) <= 1
    #             self._variable.initialized = True
    #             self._initializedNotParsed = init
    #         elif len(var["children"]) in [0, 1]:
    #             self._variable.initialized = False
    #             self._initializedNotParsed = None
    #         else:
    #             assert len(var["children"]) == 2
    #             self._variable.initialized = True
    #             self._initializedNotParsed = var["children"][1]

    def analyze(self) -> None:
        if self._was_analyzed:
            return
        self._was_analyzed = True

        if self._elem_to_parse is not None:
            print(self._elem_to_parse)
            # assert False
            self._variable.type = parse_type(self._elem_to_parse)
            self._elem_to_parse = None

        # if self._variable.initialized is not None:
        #     self._variable.expression = parse_expression(self._initializedNotParsed)
        #     self._initializedNotParsed = None
