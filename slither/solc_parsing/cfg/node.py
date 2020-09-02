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
from slither.visitors.expression.read_var import ReadVar
from slither.visitors.expression.write_var import WriteVar


class NodeSolc:
    def __init__(self, node: Node):
        self._unparsed_expression: Optional[Dict] = None
        self._node = node

    @property
    def underlying_node(self) -> Node:
        return self._node

    def add_unparsed_expression(self, expression: Dict):
        assert self._unparsed_expression is None
        self._unparsed_expression = expression

    def analyze_expressions(self, caller_context):
        if self._node.type == NodeType.VARIABLE and not self._node.expression:
            self._node.add_expression(self._node.variable_declaration.expression)
        if self._unparsed_expression:
            expression = parse_expression(self._unparsed_expression, caller_context)
            self._node.add_expression(expression)
            # self._unparsed_expression = None

        if self._node.expression:

            if self._node.type == NodeType.VARIABLE:
                # Update the expression to be an assignement to the variable
                _expression = AssignmentOperation(
                    Identifier(self._node.variable_declaration),
                    self._node.expression,
                    AssignmentOperationType.ASSIGN,
                    self._node.variable_declaration.type,
                )
                _expression.set_offset(
                    self._node.expression.source_mapping, self._node.slither
                )
                self._node.add_expression(_expression, bypass_verif_empty=True)

            expression = self._node.expression
            read_var = ReadVar(expression)
            self._node.variables_read_as_expression = read_var.result()

            write_var = WriteVar(expression)
            self._node.variables_written_as_expression = write_var.result()

            find_call = FindCalls(expression)
            self._node.calls_as_expression = find_call.result()
            self._node.external_calls_as_expressions = [
                c
                for c in self._node.calls_as_expression
                if not isinstance(c.called, Identifier)
            ]
            self._node.internal_calls_as_expressions = [
                c
                for c in self._node.calls_as_expression
                if isinstance(c.called, Identifier)
            ]
