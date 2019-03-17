import logging

from slither.core.declarations.function import Function

logger = logging.getLogger("FunctionVyper")

class FunctionVyper(Function):
    def __init__(self, function, contract):
        super(FunctionVyper, self).__init__()
        self._contract = contract
        self._name = function['name']

        self._functionNotParsed = function
        self._params_was_analyzed = False
        self._content_was_analyzed = False
        self._counter_nodes = 0

        self._counter_scope_local_variables = 0
        # variable renamed will map the solc id
        # to the variable. It only works for compact format
        # Later if an expression provides the referencedDeclaration attr
        # we can retrieve the variable
        # It only matters if two variables have the same name in the function
        # which is only possible with solc > 0.5
        self._variables_renamed = {}

    def get_key(self):
        return self.slither.get_key()
