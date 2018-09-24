import logging
from slither.slithir.operations.lvalue import OperationWithLValue
from slither.core.variables.variable import Variable

from slither.slithir.utils.utils import is_valid_lvalue, is_valid_rvalue

logger = logging.getLogger("BinaryOperationIR")

class UnaryOperationType:
    BANG =              0 # ! 
    TILD =              1 # ~ 

    @staticmethod
    def get_type(operation_type, isprefix):
        if isprefix:
            if operation_type == '!':
                return UnaryOperationType.BANG
            if operation_type == '~':
                return UnaryOperationType.TILD
        logger.error('get_type: Unknown operation type {}'.format(operation_type))
        exit(-1)

    @staticmethod
    def str(operation_type):
        if operation_type == UnaryOperationType.BANG:
            return '!'
        if operation_type == UnaryOperationType.TILD:
            return '~'

        logger.error('str: Unknown operation type {}'.format(operation_type))
        exit(-1)

class UnaryOperation(OperationWithLValue):

    def __init__(self, result, variable, operation_type):
        assert is_valid_rvalue(variable)
        assert is_valid_lvalue(result)
        super(UnaryOperation, self).__init__()
        self._variable = variable
        self._type = operation_type
        self._lvalue = result

    @property
    def read(self):
        return [self.variable]

    @property
    def variable(self):
        return self._variable

    @property
    def type_str(self):
        return UnaryOperationType.str(self._type)

    def __str__(self):
        return "{} = {} {} ".format(self.lvalue, self.type_str, self.variable)
