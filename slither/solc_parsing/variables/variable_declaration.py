import logging
import re
from typing import Dict

from slither.solc_parsing.declarations.caller_context import CallerContextExpression
from slither.solc_parsing.expressions.expression_parsing import parse_expression

from slither.core.variables.variable import Variable

from slither.solc_parsing.solidity_types.type_parsing import parse_type, UnknownType

from slither.core.solidity_types.elementary_type import (
    ElementaryType,
    NonElementaryType,
)
from slither.solc_parsing.exceptions import ParsingError

logger = logging.getLogger("VariableDeclarationSolcParsing")


class MultipleVariablesDeclaration(Exception):
    """
    This is raised on
    var (a,b) = ...
    It should occur only on local variable definition
    """

    # pylint: disable=unnecessary-pass
    pass


class VariableDeclarationSolc:
    def __init__(
        self, variable: Variable, variable_data: Dict
    ):  # pylint: disable=too-many-branches
        """
        A variable can be declared through a statement, or directly.
        If it is through a statement, the following children may contain
        the init value.
        It may be possible that the variable is declared through a statement,
        but the init value is declared at the VariableDeclaration children level
        """

        self._variable = variable
        self._was_analyzed = False
        self._elem_to_parse = None
        self._initializedNotParsed = None

        self._is_compact_ast = False

        self._reference_id = None

        if "nodeType" in variable_data:
            self._is_compact_ast = True
            nodeType = variable_data["nodeType"]
            if nodeType in [
                "VariableDeclarationStatement",
                "VariableDefinitionStatement",
            ]:
                if len(variable_data["declarations"]) > 1:
                    raise MultipleVariablesDeclaration
                init = None
                if "initialValue" in variable_data:
                    init = variable_data["initialValue"]
                self._init_from_declaration(variable_data["declarations"][0], init)
            elif nodeType == "VariableDeclaration":
                self._init_from_declaration(variable_data, variable_data.get("value", None))
            else:
                raise ParsingError(f"Incorrect variable declaration type {nodeType}")

        else:
            nodeType = variable_data["name"]

            if nodeType in [
                "VariableDeclarationStatement",
                "VariableDefinitionStatement",
            ]:
                if len(variable_data["children"]) == 2:
                    init = variable_data["children"][1]
                elif len(variable_data["children"]) == 1:
                    init = None
                elif len(variable_data["children"]) > 2:
                    raise MultipleVariablesDeclaration
                else:
                    raise ParsingError(
                        "Variable declaration without children?" + str(variable_data)
                    )
                declaration = variable_data["children"][0]
                self._init_from_declaration(declaration, init)
            elif nodeType == "VariableDeclaration":
                self._init_from_declaration(variable_data, False)
            else:
                raise ParsingError(f"Incorrect variable declaration type {nodeType}")

    @property
    def underlying_variable(self) -> Variable:
        return self._variable

    @property
    def reference_id(self) -> int:
        """
        Return the solc id. It can be compared with the referencedDeclaration attr
        Returns None if it was not parsed (legacy AST)
        """
        return self._reference_id

    def _handle_comment(self, attributes: Dict):
        if "documentation" in attributes and "text" in attributes["documentation"]:

            candidates = attributes["documentation"]["text"].split(",")

            for candidate in candidates:
                if "@custom:security non-reentrant" in candidate:
                    self._variable.is_reentrant = False

                write_protection = re.search(
                    r'@custom:security write-protection="([\w, ()]*)"', candidate
                )
                if write_protection:
                    if self._variable.write_protection is None:
                        self._variable.write_protection = []
                    self._variable.write_protection.append(write_protection.group(1))

    def _analyze_variable_attributes(self, attributes: Dict):
        if "visibility" in attributes:
            self._variable.visibility = attributes["visibility"]
        else:
            self._variable.visibility = "internal"

    def _init_from_declaration(self, var: Dict, init: bool):  # pylint: disable=too-many-branches
        if self._is_compact_ast:
            attributes = var
            self._typeName = attributes["typeDescriptions"]["typeString"]
        else:
            assert len(var["children"]) <= 2
            assert var["name"] == "VariableDeclaration"

            attributes = var["attributes"]
            self._typeName = attributes["type"]

        self._variable.name = attributes["name"]
        # self._arrayDepth = 0
        # self._isMapping = False
        # self._mappingFrom = None
        # self._mappingTo = False
        # self._initial_expression = None
        # self._type = None

        # Only for comapct ast format
        # the id can be used later if referencedDeclaration
        # is provided
        if "id" in var:
            self._reference_id = var["id"]

        if "constant" in attributes:
            self._variable.is_constant = attributes["constant"]

        if "mutability" in attributes:
            # Note: this checked is not needed if "constant" was already in attribute, but we keep it
            # for completion
            if attributes["mutability"] == "constant":
                self._variable.is_constant = True
            if attributes["mutability"] == "immutable":
                self._variable.is_immutable = True

        self._handle_comment(attributes)

        self._analyze_variable_attributes(attributes)

        if self._is_compact_ast:
            if var["typeName"]:
                self._elem_to_parse = var["typeName"]
            else:
                self._elem_to_parse = UnknownType(var["typeDescriptions"]["typeString"])
        else:
            if not var["children"]:
                # It happens on variable declared inside loop declaration
                try:
                    self._variable.type = ElementaryType(self._typeName)
                    self._elem_to_parse = None
                except NonElementaryType:
                    self._elem_to_parse = UnknownType(self._typeName)
            else:
                self._elem_to_parse = var["children"][0]

        if self._is_compact_ast:
            self._initializedNotParsed = init
            if init:
                self._variable.initialized = True
        else:
            if init:  # there are two way to init a var local in the AST
                assert len(var["children"]) <= 1
                self._variable.initialized = True
                self._initializedNotParsed = init
            elif len(var["children"]) in [0, 1]:
                self._variable.initialized = False
                self._initializedNotParsed = []
            else:
                assert len(var["children"]) == 2
                self._variable.initialized = True
                self._initializedNotParsed = var["children"][1]

    def analyze(self, caller_context: CallerContextExpression):
        # Can be re-analyzed due to inheritance
        if self._was_analyzed:
            return
        self._was_analyzed = True

        if self._elem_to_parse:
            self._variable.type = parse_type(self._elem_to_parse, caller_context)
            self._elem_to_parse = None

        if self._variable.initialized:
            self._variable.expression = parse_expression(self._initializedNotParsed, caller_context)
            self._initializedNotParsed = None
