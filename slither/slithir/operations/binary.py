import logging
from slither.slithir.operations.lvalue import OperationWithLValue
from slither.core.variables.variable import Variable
from slither.slithir.utils.utils import is_valid_lvalue, is_valid_rvalue

logger = logging.getLogger("BinaryOperationIR")

class BinaryOperationType(object):
    POWER =             0 # **
    MULTIPLICATION =    1 # *
    DIVISION =          2 # /
    MODULO =            3 # %
    ADDITION =          4 # +
    SUBTRACTION =      5 # -
    LEFT_SHIFT =        6 # <<
    RIGHT_SHIT =        7 # >>>
    AND =               8 # &
    CARET =             9 # ^
    OR =                10 # | 
    LESS =              11 # <
    GREATER =           12 # >
    LESS_EQUAL =        13 # <=
    GREATER_EQUAL =     14 # >=
    EQUAL =             15 # ==
    NOT_EQUAL =         16 # !=
    ANDAND =            17 # &&
    OROR =              18 # ||


    @staticmethod
    def get_type(operation_type):
        if operation_type == '**':
            return BinaryOperationType.POWER
        if operation_type == '*':
            return BinaryOperationType.MULTIPLICATION
        if operation_type == '/':
            return BinaryOperationType.DIVISION
        if operation_type == '%':
            return BinaryOperationType.MODULO
        if operation_type == '+':
            return BinaryOperationType.ADDITION
        if operation_type == '-':
            return BinaryOperationType.SUBTRACTION
        if operation_type == '<<':
            return BinaryOperationType.LEFT_SHIFT
        if operation_type == '>>':
            return BinaryOperationType.RIGHT_SHIT
        if operation_type == '&':
            return BinaryOperationType.AND
        if operation_type == '^':
            return BinaryOperationType.CARET
        if operation_type == '|':
            return BinaryOperationType.OR
        if operation_type == '<':
            return BinaryOperationType.LESS
        if operation_type == '>':
            return BinaryOperationType.GREATER
        if operation_type == '<=':
            return BinaryOperationType.LESS_EQUAL
        if operation_type == '>=':
            return BinaryOperationType.GREATER_EQUAL
        if operation_type == '==':
            return BinaryOperationType.EQUAL
        if operation_type == '!=':
            return BinaryOperationType.NOT_EQUAL
        if operation_type == '&&':
            return BinaryOperationType.ANDAND
        if operation_type == '||':
            return BinaryOperationType.OROR

        logger.error('get_type: Unknown operation type {})'.format(operation_type))
        exit(-1)

    @staticmethod
    def str(operation_type):
        if operation_type == BinaryOperationType.POWER:
            return '**'
        if operation_type == BinaryOperationType.MULTIPLICATION:
            return '*'
        if operation_type == BinaryOperationType.DIVISION:
            return '/'
        if operation_type == BinaryOperationType.MODULO:
            return '%'
        if operation_type == BinaryOperationType.ADDITION:
            return '+'
        if operation_type == BinaryOperationType.SUBTRACTION:
            return '-'
        if operation_type == BinaryOperationType.LEFT_SHIFT:
            return '<<'
        if operation_type == BinaryOperationType.RIGHT_SHIT:
            return '>>'
        if operation_type == BinaryOperationType.AND:
            return '&'
        if operation_type == BinaryOperationType.CARET:
            return '^'
        if operation_type == BinaryOperationType.OR:
            return '|'
        if operation_type == BinaryOperationType.LESS:
            return '<'
        if operation_type == BinaryOperationType.GREATER:
            return '>'
        if operation_type == BinaryOperationType.LESS_EQUAL:
            return '<='
        if operation_type == BinaryOperationType.GREATER_EQUAL:
            return '>='
        if operation_type == BinaryOperationType.EQUAL:
            return '=='
        if operation_type == BinaryOperationType.NOT_EQUAL:
            return '!='
        if operation_type == BinaryOperationType.ANDAND:
            return '&&'
        if operation_type == BinaryOperationType.OROR:
            return '||'
        logger.error('str: Unknown operation type {})'.format(operation_type))
        exit(-1)

class BinaryOperation(OperationWithLValue):

    def __init__(self, result, left_variable, right_variable, operation_type):
        assert is_valid_rvalue(left_variable)
        assert is_valid_rvalue(right_variable)
        assert is_valid_lvalue(result)
        super(BinaryOperation, self).__init__()
        self._variables = [left_variable, right_variable]
        self._type = operation_type
        self._lvalue = result

    @property
    def read(self):
        return [self.variable_left, self.variable_right]
    
    @property
    def get_variable(self):
        return self._variables

    @property
    def variable_left(self):
        return self._variables[0]

    @property
    def variable_right(self):
        return self._variables[1]

    @property
    def type_str(self):
        return BinaryOperationType.str(self._type)

    def __str__(self):
        return str(self.lvalue)+ ' = ' + str(self.variable_left) + ' ' + self.type_str + ' ' + str(self.variable_right)
