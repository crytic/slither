"""
    Module printing the call graph

    The call graph shows for each function,
    what are the contracts/functions called.
    The output is a dot file named filename.dot
"""

from slither.printers.abstract_printer import AbstractPrinter
from slither.core.declarations.solidity_variables import SolidityFunction
from slither.core.declarations.function import Function


class PrinterCallGraph(AbstractPrinter):
    ARGUMENT = 'call-graph'
    HELP = 'the call graph'

    def __init__(self, slither, logger):
        super(PrinterCallGraph, self).__init__(slither, logger)

        self.contracts = slither.contracts

        self.solidity_functions = set()
        self.solidity_calls = set()

    @staticmethod
    def _contract_subgraph_id(contract):
        return f'"cluster_{contract.id}_{contract.name}"'

    @staticmethod
    def _function_node_id(contract, function):
        return f'"{contract.id}_{function.full_name}"'

    def _render_contract(self, contract):
        result = f'subgraph {self._contract_subgraph_id(contract)} {{\n'
        result += f'label = "{contract.name}"\n'

        for function in contract.functions:
            result += self._render_internal_calls(contract, function)

        result += '}\n'

        return result

    def _render_internal_calls(self, contract, function):
        result = ''

        # we need to define function nodes with unique ids,
        # as it's possible that multiple contracts have same functions
        result += f'{self._function_node_id(contract, function)} [label="{function.full_name}"]\n'

        for internal_call in function.internal_calls:
            if isinstance(internal_call, (Function)):
                result += f'{self._function_node_id(contract, function)} -> {self._function_node_id(contract, internal_call)}\n'
            elif isinstance(internal_call, (SolidityFunction)):
                self.solidity_functions.add(f'"{internal_call.full_name}"')
                self.solidity_calls.add((self._function_node_id(contract, function), f'"{internal_call.full_name}"'))

        return result

    def _render_solidity_calls(self):
        result = ''

        result = 'subgraph cluster_solidity {\n'
        result += 'label = "[Solidity]"\n'

        for function in self.solidity_functions:
            result += f'{function}\n'

        result += '}\n'

        for caller, callee in self.solidity_calls:
            result += f'{caller} -> {callee}\n'

        return result

    def output(self, filename):
        """
            Output the graph in filename
            Args:
                filename(string)
        """
        if not filename.endswith('.dot'):
            filename += ".dot"
        info = 'Call Graph: ' + filename
        self.info(info)
        with open(filename, 'w') as f:
            f.write('digraph {\n')
            for contract in self.contracts:
                f.write(self._render_contract(contract))
            f.write(self._render_solidity_calls())
            f.write('}')
