import logging
from typing import Optional, Union, TypeVar, Generic

from slither.core.variables.variable import Variable

from slither.solc_parsing.solidity_types.type_parsing import parse_type

from slither.solc_parsing.expressions.expression_parsing import parse_expression
from slither.solc_parsing.types.types import VariableDeclarationStatement, Expression, VariableDeclaration, TypeName

logger = logging.getLogger("VariableDeclarationSolcParsing")


T = TypeVar('T', bound=Variable)


class VariableDeclarationSolc(Generic[T]):
    def __init__(
            self, variable: T, variable_data: Union[VariableDeclaration, VariableDeclarationStatement]
    ): # pylint: disable=too-many-branches
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

        if isinstance(variable_data, VariableDeclarationStatement):
            assert len(variable_data.variables) == 1

            self._init_from_declaration(variable_data.variables[0], variable_data.initial_value)
        elif isinstance(variable_data, VariableDeclaration):
            self._init_from_declaration(variable_data, variable_data.value)

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

    def _analyze_variable_attributes(self, var: VariableDeclaration):
        self._variable.visibility = var.visibility

    def _init_from_declaration(self, var: VariableDeclaration, init: Optional[Expression]):
        self._typeName = var.type_str
        self._variable.name = var.name

        # Only for comapct ast format
        # the id can be used later if referencedDeclaration
        # is provided
        self._reference_id = var.id

        self._variable.is_constant = var.constant
        self._analyze_variable_attributes(var)

        self._elem_to_parse = var.typename
        if not var.typename:
            self._elem_to_parse = var.type_str

        self._initializedNotParsed = init
        if init:
            self._variable.initialized = True

    def analyze(self, caller_context):
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
