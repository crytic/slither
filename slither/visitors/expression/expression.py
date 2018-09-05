import logging

from slither.core.expressions.assignmentOperation import AssignmentOperation
from slither.core.expressions.binaryOperation import BinaryOperation
from slither.core.expressions.callExpression import CallExpression
from slither.core.expressions.conditionalExpression import ConditionalExpression
from slither.core.expressions.elementaryTypeNameExpression import ElementaryTypeNameExpression
from slither.core.expressions.identifier import Identifier
from slither.core.expressions.indexAccess import IndexAccess
from slither.core.expressions.literal import Literal
from slither.core.expressions.memberAccess import MemberAccess
from slither.core.expressions.newArray import NewArray
from slither.core.expressions.newContract import NewContract
from slither.core.expressions.newElementaryType import NewElementaryType
from slither.core.expressions.tupleExpression import TupleExpression
from slither.core.expressions.typeConversion import TypeConversion
from slither.core.expressions.unaryOperation import UnaryOperation

logger = logging.getLogger("ExpressionVisitor")

class ExpressionVisitor(object):

    def __init__(self, expression):
        self._expression = expression
        self._visit_expression(self.expression)
        self._result = None

    def result(self):
        return self._result

    @property
    def expression(self):
        return self._expression

    # visit an expression
    # call pre_visit, visit_expression_name, post_visit
    def _visit_expression(self, expression):
        self._pre_visit(expression)

        if isinstance(expression, AssignmentOperation):
            self._visit_assignement_operation(expression)

        elif isinstance(expression, BinaryOperation):
            self._visit_binary_operation(expression)

        elif isinstance(expression, CallExpression):
            self._visit_call_expression(expression)

        elif isinstance(expression, ConditionalExpression):
            self._visit_conditional_expression(expression)

        elif isinstance(expression, ElementaryTypeNameExpression):
            self._visit_elementary_type_name_expression(expression)

        elif isinstance(expression, Identifier):
            self._visit_identifier(expression)

        elif isinstance(expression, IndexAccess):
            self._visit_index_access(expression)

        elif isinstance(expression, Literal):
            self._visit_literal(expression)

        elif isinstance(expression, MemberAccess):
            self._visit_member_access(expression)

        elif isinstance(expression, NewArray):
            self._visit_new_array(expression)

        elif isinstance(expression, NewContract):
            self._visit_new_contract(expression)

        elif isinstance(expression, NewElementaryType):
            self._visit_new_elementary_type(expression)

        elif isinstance(expression, TupleExpression):
            self._visit_tuple_expression(expression)

        elif isinstance(expression, TypeConversion):
            self._visit_type_conversion(expression)

        elif isinstance(expression, UnaryOperation):
            self._visit_unary_operation(expression)

        elif expression is None:
            pass

        else:
            logger.error('Expression not handled: {}'.format(expression))
            exit(-1)

        self._post_visit(expression)

    # visit_expression_name

    def _visit_assignement_operation(self, expression):
        self._visit_expression(expression.expression_left)
        self._visit_expression(expression.expression_right)

    def _visit_binary_operation(self, expression):
        self._visit_expression(expression.expression_left)
        self._visit_expression(expression.expression_right)

    def _visit_call_expression(self, expression):
        self._visit_expression(expression.called)
        for arg in expression.arguments:
            if arg:
                self._visit_expression(arg)

    def _visit_conditional_expression(self, expression):
        self._visit_expression(expression.if_expression)
        self._visit_expression(expression.else_expression)
        self._visit_expression(expression.then_expression)

    def _visit_elementary_type_name_expression(self, expression):
        pass

    def _visit_identifier(self, expression):
        pass

    def _visit_index_access(self, expression):
        self._visit_expression(expression.expression_left)
        self._visit_expression(expression.expression_right)

    def _visit_literal(self, expression):
        pass

    def _visit_member_access(self, expression):
        self._visit_expression(expression.expression)

    def _visit_new_array(self, expression):
        pass

    def _visit_new_contract(self, expression):
        pass

    def _visit_new_elementary_type(self, expression):
        pass

    def _visit_tuple_expression(self, expression):
        for e in expression.expressions:
            if e:
                self._visit_expression(e)

    def _visit_type_conversion(self, expression):
        self._visit_expression(expression.expression)

    def _visit_unary_operation(self, expression):
        self._visit_expression(expression.expression)

    # pre visit

    def _pre_visit(self, expression):
        if isinstance(expression, AssignmentOperation):
            self._pre_assignement_operation(expression)

        elif isinstance(expression, BinaryOperation):
            self._pre_binary_operation(expression)

        elif isinstance(expression, CallExpression):
            self._pre_call_expression(expression)

        elif isinstance(expression, ConditionalExpression):
            self._pre_conditional_expression(expression)

        elif isinstance(expression, ElementaryTypeNameExpression):
            self._pre_elementary_type_name_expression(expression)

        elif isinstance(expression, Identifier):
            self._pre_identifier(expression)

        elif isinstance(expression, IndexAccess):
            self._pre_index_access(expression)

        elif isinstance(expression, Literal):
            self._pre_literal(expression)

        elif isinstance(expression, MemberAccess):
            self._pre_member_access(expression)

        elif isinstance(expression, NewArray):
            self._pre_new_array(expression)

        elif isinstance(expression, NewContract):
            self._pre_new_contract(expression)

        elif isinstance(expression, NewElementaryType):
            self._pre_new_elementary_type(expression)

        elif isinstance(expression, TupleExpression):
            self._pre_tuple_expression(expression)

        elif isinstance(expression, TypeConversion):
            self._pre_type_conversion(expression)

        elif isinstance(expression, UnaryOperation):
            self._pre_unary_operation(expression)

        elif expression is None:
            pass

        else:
            logger.error('Expression not handled: {}'.format(expression))
            exit(-1)

    # pre_expression_name

    def _pre_assignement_operation(self, expression):
        pass

    def _pre_binary_operation(self, expression):
        pass

    def _pre_call_expression(self, expression):
        pass

    def _pre_conditional_expression(self, expression):
        pass

    def _pre_elementary_type_name_expression(self, expression):
        pass

    def _pre_identifier(self, expression):
        pass

    def _pre_index_access(self, expression):
        pass

    def _pre_literal(self, expression):
        pass

    def _pre_member_access(self, expression):
        pass

    def _pre_new_array(self, expression):
        pass

    def _pre_new_contract(self, expression):
        pass

    def _pre_new_elementary_type(self, expression):
        pass

    def _pre_tuple_expression(self, expression):
        pass

    def _pre_type_conversion(self, expression):
        pass

    def _pre_unary_operation(self, expression):
        pass

    # post visit

    def _post_visit(self, expression):
        if isinstance(expression, AssignmentOperation):
            self._post_assignement_operation(expression)

        elif isinstance(expression, BinaryOperation):
            self._post_binary_operation(expression)

        elif isinstance(expression, CallExpression):
            self._post_call_expression(expression)

        elif isinstance(expression, ConditionalExpression):
            self._post_conditional_expression(expression)

        elif isinstance(expression, ElementaryTypeNameExpression):
            self._post_elementary_type_name_expression(expression)

        elif isinstance(expression, Identifier):
            self._post_identifier(expression)

        elif isinstance(expression, IndexAccess):
            self._post_index_access(expression)

        elif isinstance(expression, Literal):
            self._post_literal(expression)

        elif isinstance(expression, MemberAccess):
            self._post_member_access(expression)

        elif isinstance(expression, NewArray):
            self._post_new_array(expression)

        elif isinstance(expression, NewContract):
            self._post_new_contract(expression)

        elif isinstance(expression, NewElementaryType):
            self._post_new_elementary_type(expression)

        elif isinstance(expression, TupleExpression):
            self._post_tuple_expression(expression)

        elif isinstance(expression, TypeConversion):
            self._post_type_conversion(expression)

        elif isinstance(expression, UnaryOperation):
            self._post_unary_operation(expression)

        elif expression is None:
            pass

        else:
            logger.error('Expression not handled: {}'.format(expression))
            exit(-1)

    # post_expression_name

    def _post_assignement_operation(self, expression):
        pass

    def _post_binary_operation(self, expression):
        pass

    def _post_call_expression(self, expression):
        pass

    def _post_conditional_expression(self, expression):
        pass

    def _post_elementary_type_name_expression(self, expression):
        pass

    def _post_identifier(self, expression):
        pass

    def _post_index_access(self, expression):
        pass

    def _post_literal(self, expression):
        pass

    def _post_member_access(self, expression):
        pass

    def _post_new_array(self, expression):
        pass

    def _post_new_contract(self, expression):
        pass

    def _post_new_elementary_type(self, expression):
        pass

    def _post_tuple_expression(self, expression):
        pass

    def _post_type_conversion(self, expression):
        pass

    def _post_unary_operation(self, expression):
        pass


