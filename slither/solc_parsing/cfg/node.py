from slither.core.cfg.node import Node
from slither.core.cfg.node import NodeType
from slither.solc_parsing.expressions.expression_parsing import parse_expression
from slither.visitors.expression.read_var import ReadVar
from slither.visitors.expression.write_var import WriteVar
from slither.visitors.expression.find_calls import FindCalls

from slither.visitors.expression.export_values import ExportValues
from slither.core.declarations.solidity_variables import SolidityVariable, SolidityFunction
from slither.core.declarations.function import Function

from slither.core.variables.state_variable import StateVariable

from slither.core.expressions.identifier import Identifier
from slither.core.expressions.assignment_operation import AssignmentOperation, AssignmentOperationType

class NodeSolc(Node):

    def __init__(self, nodeType, nodeId):
        super(NodeSolc, self).__init__(nodeType, nodeId)
        self._unparsed_expression = None

    def add_unparsed_expression(self, expression):
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
                #print(self.variable_declaration)
                _expression = AssignmentOperation(Identifier(self.variable_declaration),
                                                  self.expression,
                                                  AssignmentOperationType.ASSIGN,
                                                  self.variable_declaration.type)
                _expression.set_offset(self.expression.source_mapping, self.slither)
                self._expression = _expression

            expression = self.expression
            pp = ReadVar(expression)
            self._expression_vars_read = pp.result()

#            self._vars_read = [item for sublist in vars_read for item in sublist]
#            self._state_vars_read = [x for x in self.variables_read if\
#                                     isinstance(x, (StateVariable))]
#            self._solidity_vars_read = [x for x in self.variables_read if\
#                                        isinstance(x, (SolidityVariable))]

            pp = WriteVar(expression)
            self._expression_vars_written = pp.result()

#            self._vars_written = [item for sublist in vars_written for item in sublist]
#            self._state_vars_written = [x for x in self.variables_written if\
#                                        isinstance(x, StateVariable)]

            pp = FindCalls(expression)
            self._expression_calls = pp.result()
            self._external_calls_as_expressions = [c for c in self.calls_as_expression if not isinstance(c.called, Identifier)]
            self._internal_calls_as_expressions = [c for c in self.calls_as_expression if isinstance(c.called, Identifier)]
            

