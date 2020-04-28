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


class NodeSolc(Node):
    def __init__(self, node_type: NodeType, node_id: int):
        super(NodeSolc, self).__init__(node_type, node_id)
        self._unparsed_expression: Optional[Dict] = None

    def add_unparsed_expression(self, expression: Dict):
        assert self._unparsed_expression is None
        self._unparsed_expression = expression

    def analyze_expressions(self, caller_context):
        if self.type == NodeType.VARIABLE and not self._expression:
            self._expression = self.variable_declaration.expression
        if self._unparsed_expression:
            expression = parse_expression(self._unparsed_expression, caller_context)
            self._expression = expression
            self._unparsed_expression = None

        if self.expression:

            if self.type == NodeType.VARIABLE:
                # Update the expression to be an assignement to the variable
                _expression = AssignmentOperation(
                    Identifier(self.variable_declaration),
                    self.expression,
                    AssignmentOperationType.ASSIGN,
                    self.variable_declaration.type,
                )
                _expression.set_offset(self.expression.source_mapping, self.slither)
                self._expression = _expression

            expression = self.expression
            read_var = ReadVar(expression)
            self._expression_vars_read = read_var.result()

            write_var = WriteVar(expression)
            self._expression_vars_written = write_var.result()

            find_call = FindCalls(expression)
            self._expression_calls = find_call.result()
            self._external_calls_as_expressions = [
                c for c in self.calls_as_expression if not isinstance(c.called, Identifier)
            ]
            self._internal_calls_as_expressions = [
                c for c in self.calls_as_expression if isinstance(c.called, Identifier)
            ]
