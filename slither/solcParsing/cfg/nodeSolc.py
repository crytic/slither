from slither.core.cfg.node import Node
from slither.solcParsing.expressions.expressionParsing import parse_expression
from slither.visitors.expression.readVar import ReadVar
from slither.visitors.expression.writeVar import WriteVar
from slither.visitors.expression.findCalls import FindCalls

from slither.visitors.expression.exportValues import ExportValues
from slither.core.declarations.solidityVariables import SolidityVariable, SolidityFunction
from slither.core.declarations.function import Function


from slither.core.variables.stateVariable import StateVariable

class NodeSolc(Node):

    def __init__(self, nodeType, nodeId):
        super(NodeSolc, self).__init__(nodeType, nodeId)
        self._unparsed_expression = None

    def add_unparsed_expression(self, expression):
        assert self._unparsed_expression is None
        self._unparsed_expression = expression

    def analyze_expressions(self, caller_context):
        if self._unparsed_expression:
            expression = parse_expression(self._unparsed_expression, caller_context)

            pp = ReadVar(expression)
            self._expression_vars_read = pp.result()
            vars_read = [ExportValues(v).result() for v in self._expression_vars_read]
            self._vars_read = [item for sublist in vars_read for item in sublist]
            self._state_vars_read = [x for x in self.variables_read if\
                                     isinstance(x, (StateVariable))]
            self._solidity_vars_read = [x for x in self.variables_read if\
                                        isinstance(x, (SolidityVariable))]

            pp = WriteVar(expression)
            self._expression_vars_written = pp.result()
            vars_written = [ExportValues(v).result() for v in self._expression_vars_written]
            self._vars_written = [item for sublist in vars_written for item in sublist]
            self._state_vars_written = [x for x in self.variables_written if\
                                        isinstance(x, StateVariable)]

            pp = FindCalls(expression)
            self._expression_calls = pp.result()
            calls = [ExportValues(c).result() for c in self.calls_as_expression]
            calls = [item for sublist in calls for item in sublist]
            self._calls = [c for c in calls if isinstance(c, (Function, SolidityFunction))]

            self._unparsed_expression = None
            self._expression = expression
