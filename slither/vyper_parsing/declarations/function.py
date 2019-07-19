"""
"""
import logging

from slither.core.declarations.function import Function
from ..variables.local_variable import LocalVariableVyper

logger = logging.getLogger("FunctionSolc")

class FunctionVyper(Function):
    """
    """
    # elems = [(type, name)]

    def __init__(self, function, contract):
        super(FunctionVyper, self).__init__()

        self._function_not_parsed = function
        self._contract = contract
        self._contract_declarer = contract

        self._name = function['name']

        self._analyze_decorators()
        self._analyze_args()
        self._analyze_return()


    # endregion
    ###################################################################################
    ###################################################################################
    # region Analyses
    ###################################################################################
    ###################################################################################

    def _analyze_decorators(self):

        self._payable = False
        for decorator in self._function_not_parsed['decorator_list']:
            if decorator['id'] == 'constant':
                self._view = True
            if decorator['id'] == 'public':
                self._visibility = 'public'
            if decorator['id'] == 'private':
                self._visibility = 'private'
            if decorator['id'] == 'payable':
                self._payable = True

    def _analyze_args(self):

        if self._function_not_parsed['args'] is None:
            return
        for variable in self._function_not_parsed['args']['args']:
            local_variable = LocalVariableVyper(variable)

            local_variable.set_offset(None, self.slither)
            self._variables[local_variable.name] = local_variable
            self._parameters.append(local_variable)

    def _analyze_return(self):

        if self._function_not_parsed['returns'] is None:
            return

        for variable in self._function_not_parsed['args']['args']:
            local_variable = LocalVariableVyper(variable)

            local_variable.set_offset(None, self.slither)
            self._variables[local_variable.name] = local_variable
            self._returns.append(local_variable)

