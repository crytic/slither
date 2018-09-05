import logging
from slither.core.expressions.expressionTyped import ExpressionTyped
from slither.core.expressions.expression import Expression


logger = logging.getLogger("AssignmentOperation")

class AssignmentOperationType(object):
    ASSIGN =                0 # =
    ASSIGN_OR =             1 # |=
    ASSIGN_CARET =          2 # ^=
    ASSIGN_AND =            3 # &=
    ASSIGN_LEFT_SHIFT =     4 # <<=
    ASSIGN_RIGHT_SHIFT =    5 # >>=
    ASSIGN_ADDITION =       6 # +=
    ASSIGN_SUBSTRACTION =   7 # -=
    ASSIGN_MULTIPLICATION = 8 # *=
    ASSIGN_DIVISION =       9 # /=
    ASSIGN_MODULO =         10 # %=

    @staticmethod
    def get_type(operation_type):
        if operation_type == '=':
            return AssignmentOperationType.ASSIGN
        if operation_type == '|=':
            return AssignmentOperationType.ASSIGN_OR
        if operation_type == '^=':
            return AssignmentOperationType.ASSIGN_CARET
        if operation_type == '&=':
            return AssignmentOperationType.ASSIGN_AND
        if operation_type == '<<=':
            return AssignmentOperationType.ASSIGN_LEFT_SHIFT
        if operation_type == '>>=':
            return AssignmentOperationType.ASSIGN_RIGHT_SHIFT
        if operation_type == '+=':
            return AssignmentOperationType.ASSIGN_ADDITION
        if operation_type == '-=':
            return AssignmentOperationType.ASSIGN_SUBSTRACTION
        if operation_type == '*=':
            return AssignmentOperationType.ASSIGN_MULTIPLICATION
        if operation_type == '/=':
            return AssignmentOperationType.ASSIGN_DIVISION
        if operation_type == '%=':
            return AssignmentOperationType.ASSIGN_MODULO

        logger.error('get_type: Unknown operation type {})'.format(operation_type))
        exit(-1)

    @staticmethod
    def str(operation_type):
        if operation_type == AssignmentOperationType.ASSIGN:
            return '='
        if operation_type == AssignmentOperationType.ASSIGN_OR:
            return '|='
        if operation_type == AssignmentOperationType.ASSIGN_CARET:
            return '^='
        if operation_type == AssignmentOperationType.ASSIGN_AND:
            return '&='
        if operation_type == AssignmentOperationType.ASSIGN_LEFT_SHIFT:
            return '<<='
        if operation_type == AssignmentOperationType.ASSIGN_RIGHT_SHIFT:
            return '>>='
        if operation_type == AssignmentOperationType.ASSIGN_ADDITION:
            return '+='
        if operation_type == AssignmentOperationType.ASSIGN_SUBSTRACTION:
            return '-='
        if operation_type == AssignmentOperationType.ASSIGN_MULTIPLICATION:
            return '*='
        if operation_type == AssignmentOperationType.ASSIGN_DIVISION:
            return '/='
        if operation_type == AssignmentOperationType.ASSIGN_MODULO:
            return '%='

        logger.error('str: Unknown operation type {})'.format(operation_type))
        exit(-1)

class AssignmentOperation(ExpressionTyped):

    def __init__(self, left_expression, right_expression, expression_type, expression_return_type):
        assert isinstance(left_expression, Expression)
        assert isinstance(right_expression, Expression)
        super(AssignmentOperation, self).__init__()
        left_expression.set_lvalue()
        self._expressions = [left_expression, right_expression]
        self._type = expression_type
        self._expression_return_type = expression_return_type

    @property
    def expressions(self):
        return self._expressions

    @property
    def expression_return_type(self):
        return self._expression_return_type

    @property
    def expression_left(self):
        return self._expressions[0]

    @property
    def expression_right(self):
        return self._expressions[1]

    @property
    def type(self):
        return self._type

    @property
    def type_str(self):
        return AssignmentOperationType.str(self._type)

    def __str__(self):
        return str(self.expression_left) + " "+ self.type_str  + " " + str(self.expression_right)
