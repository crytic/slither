from typing import Optional, Dict

from slither.core.cfg.node import Node
from slither.core.cfg.node import NodeType
from slither.core.expressions.assignment_operation import (
    AssignmentOperation,
    AssignmentOperationType,
)
from slither.core.expressions.identifier import Identifier
from slither.solc_parsing.expressions.expression_parsing import parse_expression
from slither.visitors.expression.find_calls import FindCalls
from slither.solc_parsing.yul.parse_yul import parse_yul
from slither.visitors.expression.read_var import ReadVar
from slither.visitors.expression.write_var import WriteVar


class NodeSolc:
    def __init__(self, node: Node):
        self._unparsed_expression: Optional[Dict] = None
        self._node = node
        self._unparsed_yul_expression = None

        """
        todo this should really go somewhere else, but until
        that happens I'm setting it to None for performance
        """
        self._yul_local_variables = None
        self._yul_local_functions = None
        self._yul_path = None

    @property
    def underlying_node(self) -> Node:
        return self._node

    def set_yul_root(self, func):
        self._yul_path = [func.name, f"asm_{func._counter_asm_nodes}"]

    def set_yul_child(self, parent, cur):
        self._yul_path = parent.yul_path +  [cur]

    @property
    def yul_path(self):
        return self._yul_path

    def format_canonical_yul_name(self, name, off=None):
        return ".".join(self._yul_path[:off] + [name])

    def add_yul_local_variable(self, var):
        if not self._yul_local_variables:
            self._yul_local_variables = []
        self._yul_local_variables.append(var)

    def get_yul_local_variable_from_name(self, variable_name):
        return next((v for v in self._yul_local_variables if v.name == variable_name), None)

    def add_yul_local_function(self, func):
        if not self._yul_local_functions:
            self._yul_local_functions = []
        self._yul_local_functions.append(func)

    def get_yul_local_function_from_name(self, func_name):
        return next((v for v in self._yul_local_functions if v.name == func_name), None)

    def add_unparsed_expression(self, expression: Dict):
        assert self._unparsed_expression is None
        self._unparsed_expression = expression

    def add_unparsed_yul_expression(self, root, expression):
        assert self._unparsed_expression is None
        self._unparsed_yul_expression = (root, expression)

    def analyze_expressions(self, caller_context):
        if self._node.type == NodeType.VARIABLE and not self._node.expression:
            self._node.add_expression(self._node.variable_declaration.expression)
        if self._unparsed_expression:
            expression = parse_expression(self._unparsed_expression, caller_context)
            self._node.add_expression(expression)
            # self._unparsed_expression = None

        if self._unparsed_yul_expression:
            expression = parse_yul(self._unparsed_yul_expression[0], self, self._unparsed_yul_expression[1])
            self._expression = expression
            self._unparsed_yul_expression = None

        if self._node.expression:

            if self._node.type == NodeType.VARIABLE:
                # Update the expression to be an assignement to the variable
                _expression = AssignmentOperation(
                    Identifier(self._node.variable_declaration),
                    self._node.expression,
                    AssignmentOperationType.ASSIGN,
                    self._node.variable_declaration.type,
                )
                _expression.set_offset(self._node.expression.source_mapping, self._node.slither)
                self._node.add_expression(_expression, bypass_verif_empty=True)

            expression = self._node.expression
            read_var = ReadVar(expression)
            self._node.variables_read_as_expression = read_var.result()

            write_var = WriteVar(expression)
            self._node.variables_written_as_expression = write_var.result()

            find_call = FindCalls(expression)
            self._node.calls_as_expression = find_call.result()
            self._node.external_calls_as_expressions = [
                c for c in self._node.calls_as_expression if not isinstance(c.called, Identifier)
            ]
            self._node.internal_calls_as_expressions = [
                c for c in self._node.calls_as_expression if isinstance(c.called, Identifier)
            ]
