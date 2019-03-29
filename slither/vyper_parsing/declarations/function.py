import logging

from slither.core.declarations.function import Function

logger = logging.getLogger("FunctionVyper")

class FunctionVyper(Function):
    def __init__(self, function, function_sig, contract):
        super(FunctionVyper, self).__init__()
        self._contract = contract
        self._sig = function_sig
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


    def analyze_params(self):
        # Can be re-analyzed due to inheritance
        if self._params_was_analyzed:
            return

        self._params_was_analyzed = True

        self._analyze_attributes()

        params = self._functionNotParsed['args']
        returns = self._functionNotParsed['returns']

        if params:
            self._parse_params(params)
        if returns:
            self._parse_returns(returns)

    def _analyze_attributes(self):
        if self._name == '__init__':
            self._is_constructor = True
        self._payable = self._sig.payable

        if self._sig.private:
            self._visibility = 'private'
        else:
            self._visibility = 'public'
        if self._sig.const:
            self._view = True

    def _parse_params(self, params):
        print(self._sig.args)

    def _parse_returns(self, returns):
        pass

    def generate_slithir_and_analyze(self):
        pass

    def generate_slithir_ssa(self, all_ssa_state_variables_instances):
        pass

    def get_last_ssa_state_variables_instances(self):
        pass
