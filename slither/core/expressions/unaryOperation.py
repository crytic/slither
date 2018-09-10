import logging
from slither.core.expressions.expressionTyped import ExpressionTyped
from slither.core.expressions.expression import Expression
from slither.core.solidityTypes.type import Type

logger = logging.getLogger("UnaryOperation")

class UnaryOperationType:
    BANG =              0 # ! 
    TILD =              1 # ~ 
    DELETE =            2 # delete
    PLUSPLUS_PRE =      3 # ++ 
    MINUSMINUS_PRE =    4 # --
    PLUSPLUS_POST =     5 # ++
    MINUSMINUS_POST =   6 # --
    PLUS_PRE =          7 # for stuff like uint(+1)
    MINUS_PRE =         8 # for stuff like uint(-1)

    @staticmethod
    def get_type(operation_type, isprefix):
        if isprefix:
            if operation_type == '!':
                return UnaryOperationType.BANG
            if operation_type == '~':
                return UnaryOperationType.TILD
            if operation_type == 'delete':
                return UnaryOperationType.DELETE
            if operation_type == '++':
                return UnaryOperationType.PLUSPLUS_PRE
            if operation_type == '--':
                return UnaryOperationType.MINUSMINUS_PRE
            if operation_type == '+':
                return UnaryOperationType.PLUS_PRE
            if operation_type == '-':
                return UnaryOperationType.MINUS_PRE
        else:
            if operation_type == '++':
                return UnaryOperationType.PLUSPLUS_POST
            if operation_type == '--':
                return UnaryOperationType.MINUSMINUS_POST
        logger.error('get_type: Unknown operation type {}'.format(operation_type))
        exit(-1)

    @staticmethod
    def str(operation_type):
        if operation_type == UnaryOperationType.BANG:
            return '!'
        if operation_type == UnaryOperationType.TILD:
            return '~'
        if operation_type == UnaryOperationType.DELETE:
            return 'delete'
        if operation_type == UnaryOperationType.PLUS_PRE:
            return '+'
        if operation_type == UnaryOperationType.MINUS_PRE:
            return '-'
        if operation_type in [UnaryOperationType.PLUSPLUS_PRE, UnaryOperationType.PLUSPLUS_POST]:
            return '++'
        if operation_type in [UnaryOperationType.MINUSMINUS_PRE, UnaryOperationType.MINUSMINUS_POST]:
            return '--'

        logger.error('str: Unknown operation type {}'.format(operation_type))
        exit(-1)

    @staticmethod
    def is_prefix(operation_type):
        if operation_type in [UnaryOperationType.BANG,
                              UnaryOperationType.TILD,
                              UnaryOperationType.DELETE,
                              UnaryOperationType.PLUSPLUS_PRE,
                              UnaryOperationType.MINUSMINUS_PRE,
                              UnaryOperationType.PLUS_PRE,
                              UnaryOperationType.MINUS_PRE]:
            return True
        elif operation_type in [UnaryOperationType.PLUSPLUS_POST, UnaryOperationType.MINUSMINUS_POST]:
            return False

        logger.error('is_prefix: Unknown operation type {}'.format(operation_type))
        exit(-1)

class UnaryOperation(ExpressionTyped):

    def __init__(self, expression, expression_type):
        assert isinstance(expression, Expression)
        super(UnaryOperation, self).__init__()
        self._expression = expression
        self._type = expression_type
        if expression_type in [UnaryOperationType.DELETE,
                               UnaryOperationType.PLUSPLUS_PRE,
                               UnaryOperationType.MINUSMINUS_PRE,
                               UnaryOperationType.PLUSPLUS_POST,
                               UnaryOperationType.MINUSMINUS_POST,
                               UnaryOperationType.PLUS_PRE,
                               UnaryOperationType.MINUS_PRE]:
            expression.set_lvalue()

    @property
    def expression(self):
        return self._expression

    @property
    def type_str(self):
        return UnaryOperationType.str(self._type)

    @property
    def is_prefix(self):
        return UnaryOperationType.is_prefix(self._type)

    def __str__(self):
        if self.is_prefix:
            return self.type_str + ' ' + str(self._expression)
        else:
            return str(self._expression) + ' ' + self.type_str

