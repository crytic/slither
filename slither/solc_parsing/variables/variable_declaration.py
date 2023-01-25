import logging
import re
from typing import Generic, Union, Optional, TypeVar

from slither.solc_parsing.declarations.caller_context import CallerContextExpression
from slither.solc_parsing.expressions.expression_parsing import parse_expression

from slither.core.variables.variable import Variable

from slither.solc_parsing.solidity_types.type_parsing import parse_type, UnknownType

from slither.core.solidity_types.elementary_type import (
    ElementaryType,
    NonElementaryType,
)
from slither.solc_parsing.types.types import VariableDeclaration, VariableDeclarationStatement, TypeName, Expression

logger = logging.getLogger("VariableDeclarationSolcParsing")

T = TypeVar('T', bound=Variable)

class MultipleVariablesDeclaration(Exception):
    """
    This is raised on
    var (a,b) = ...
    It should occur only on local variable definition
    """

    # pylint: disable=unnecessary-pass
    pass


class VariableDeclarationSolc(Generic[T]):
    def __init__(
        self, variable: T, variable_decl: Union[VariableDeclaration, VariableDeclarationStatement]
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
        self._elem_to_parse: Optional[Union[TypeName, str]] = None
        self._initializedNotParsed = None

        self._reference_id = None

        if isinstance(variable_decl, VariableDeclarationStatement):
            assert len(variable_decl.variables) == 1

            self._init_from_declaration(variable_decl.variables[0], variable_decl.initial_value)
        elif isinstance(variable_decl, VariableDeclaration):
            self._init_from_declaration(variable_decl, variable_decl.value)

    @property
    def underlying_variable(self) -> T:
        return self._variable

    @property
    def reference_id(self) -> int:
        """
        Return the solc id. It can be compared with the referencedDeclaration attr
        Returns None if it was not parsed (legacy AST)
        """
        return self._reference_id

    def _handle_comment(self, var: VariableDeclaration):
        if var.documentation:
            candidates = var.documentation.split(",")

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

    def _analyze_variable_attributes(self, var: VariableDeclaration):
        self._variable.visibility = var.visibility
        self._variable.is_constant = var.mutability == "constant"
        self._variable.is_immutable = var.mutability == "immutable"

    def _init_from_declaration(self, var: VariableDeclaration, init: Optional[Expression]):
        self._typeName = var.type_str
        self._variable.name = var.name
        self._reference_id = var.id

        self._handle_comment(var)
        self._analyze_variable_attributes(var)

        self._elem_to_parse = var.typename
        if not var.typename:
            self._elem_to_parse = UnknownType(var.type_str)

        self._initializedNotParsed = init
        if init:
            self._variable.initialized = True


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
