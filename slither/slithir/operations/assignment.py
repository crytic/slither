import logging

from slither.slithir.operations.lvalue import OperationWithLValue
from slither.core.variables.variable import Variable
from slither.core.declarations.function import Function
from slither.slithir.utils.utils import is_valid_lvalue, is_valid_rvalue

logger = logging.getLogger("AssignmentOperationIR")

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

class Assignment(OperationWithLValue):

    def __init__(self, left_variable, right_variable, variable_type, variable_return_type):
        #print(type(right_variable))
        #print(type(left_variable))
        assert is_valid_lvalue(left_variable)
        assert is_valid_rvalue(right_variable) or\
               (isinstance(right_variable, Function) and variable_type == AssignmentOperationType.ASSIGN)
        super(Assignment, self).__init__()
        self._variables = [left_variable, right_variable]
        self._lvalue = left_variable
        self._rvalue = right_variable
        self._type = variable_type
        self._variable_return_type = variable_return_type

    @property
    def variables(self):
        return list(self._variables)

    @property
    def read(self):
        return list(self.variables)
    
    @property
    def variable_return_type(self):
        return self._variable_return_type

    @property
    def rvalue(self):
        return self._rvalue

    @property
    def type_str(self):
        return AssignmentOperationType.str(self._type)

    def __str__(self):
        return '{} {} {}'.format(self.lvalue, self.type_str, self.rvalue)
