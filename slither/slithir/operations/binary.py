import logging
from slither.slithir.operations.lvalue import OperationWithLValue
from slither.core.variables.variable import Variable
from slither.slithir.utils.utils import is_valid_lvalue, is_valid_rvalue

logger = logging.getLogger("BinaryOperationIR")

class BinaryType(object):
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
    def return_bool(operation_type):
        return operation_type in [BinaryType.OROR,
                                  BinaryType.ANDAND,
                                  BinaryType.LESS,
                                  BinaryType.GREATER,
                                  BinaryType.LESS_EQUAL,
                                  BinaryType.GREATER_EQUAL,
                                  BinaryType.EQUAL,
                                  BinaryType.NOT_EQUAL]

    @staticmethod
    def get_type(operation_type):
        if operation_type == '**':
            return BinaryType.POWER
        if operation_type == '*':
            return BinaryType.MULTIPLICATION
        if operation_type == '/':
            return BinaryType.DIVISION
        if operation_type == '%':
            return BinaryType.MODULO
        if operation_type == '+':
            return BinaryType.ADDITION
        if operation_type == '-':
            return BinaryType.SUBTRACTION
        if operation_type == '<<':
            return BinaryType.LEFT_SHIFT
        if operation_type == '>>':
            return BinaryType.RIGHT_SHIT
        if operation_type == '&':
            return BinaryType.AND
        if operation_type == '^':
            return BinaryType.CARET
        if operation_type == '|':
            return BinaryType.OR
        if operation_type == '<':
            return BinaryType.LESS
        if operation_type == '>':
            return BinaryType.GREATER
        if operation_type == '<=':
            return BinaryType.LESS_EQUAL
        if operation_type == '>=':
            return BinaryType.GREATER_EQUAL
        if operation_type == '==':
            return BinaryType.EQUAL
        if operation_type == '!=':
            return BinaryType.NOT_EQUAL
        if operation_type == '&&':
            return BinaryType.ANDAND
        if operation_type == '||':
            return BinaryType.OROR

        logger.error('get_type: Unknown operation type {})'.format(operation_type))
        exit(-1)

    @staticmethod
    def str(operation_type):
        if operation_type == BinaryType.POWER:
            return '**'
        if operation_type == BinaryType.MULTIPLICATION:
            return '*'
        if operation_type == BinaryType.DIVISION:
            return '/'
        if operation_type == BinaryType.MODULO:
            return '%'
        if operation_type == BinaryType.ADDITION:
            return '+'
        if operation_type == BinaryType.SUBTRACTION:
            return '-'
        if operation_type == BinaryType.LEFT_SHIFT:
            return '<<'
        if operation_type == BinaryType.RIGHT_SHIT:
            return '>>'
        if operation_type == BinaryType.AND:
            return '&'
        if operation_type == BinaryType.CARET:
            return '^'
        if operation_type == BinaryType.OR:
            return '|'
        if operation_type == BinaryType.LESS:
            return '<'
        if operation_type == BinaryType.GREATER:
            return '>'
        if operation_type == BinaryType.LESS_EQUAL:
            return '<='
        if operation_type == BinaryType.GREATER_EQUAL:
            return '>='
        if operation_type == BinaryType.EQUAL:
            return '=='
        if operation_type == BinaryType.NOT_EQUAL:
            return '!='
        if operation_type == BinaryType.ANDAND:
            return '&&'
        if operation_type == BinaryType.OROR:
            return '||'
        logger.error('str: Unknown operation type {})'.format(operation_type))
        exit(-1)

class Binary(OperationWithLValue):

    def __init__(self, result, left_variable, right_variable, operation_type):
        assert is_valid_rvalue(left_variable)
        assert is_valid_rvalue(right_variable)
        assert is_valid_lvalue(result)
        super(Binary, self).__init__()
        self._variables = [left_variable, right_variable]
        self._type = operation_type
        self._lvalue = result
        if BinaryType.return_bool(operation_type):
            result.set_type('bool')
        else:
            result.set_type(left_variable.type)

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
    def type(self):
        return self._type

    @property
    def type_str(self):
        return BinaryType.str(self._type)

    def __str__(self):
        return '{}({}) = {} {} {}'.format(str(self.lvalue),
                                          self.lvalue.type,
                                          self.variable_left,
                                          self.type_str,
                                          self.variable_right)
