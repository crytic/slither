"""
    Module printing the call graph

    The call graph shows for each function,
    what are the contracts/functions called.
    The output is a dot file named filename.dot
"""

from slither.printers.abstract_printer import AbstractPrinter
from slither.core.declarations.solidity_variables import SolidityFunction
from slither.core.declarations.function import Function
from slither.core.declarations.contract import Contract
from slither.core.expressions.member_access import MemberAccess
from slither.core.expressions.identifier import Identifier
from slither.core.variables.variable import Variable
from slither.core.solidity_types.user_defined_type import UserDefinedType

# return unique id for contract to use as subgraph name
def _contract_subgraph(contract):
    return f'cluster_{contract.id}_{contract.name}'

# return unique id for contract function to use as node name
def _function_node(contract, function):
    return f'{contract.id}_{function.name}'

# return unique id for solidity function to use as node name
def _solidity_function_node(solidity_function):
    return f'{solidity_function.name}'

# return dot language string to add graph edge
def _edge(from_node, to_node):
    return f'"{from_node}" -> "{to_node}"'

# return dot language string to add graph node (with optional label)
def _node(node, label=None):
    return ' '.join((
        f'"{node}"',
        f'[label="{label}"]' if label is not None else '',
    ))

class PrinterCallGraph(AbstractPrinter):
    ARGUMENT = 'call-graph'
    HELP = 'the call graph'

    def __init__(self, slither, logger):
        super(PrinterCallGraph, self).__init__(slither, logger)

        self.contract_functions = {} # contract -> contract functions nodes
        self.contract_calls = {} # contract -> contract calls edges

        for contract in slither.contracts:
            self.contract_functions[contract] = set()
            self.contract_calls[contract] = set()

        self.solidity_functions = set() # solidity function nodes
        self.solidity_calls = set() # solidity calls edges

        self.external_calls = set() # external calls edges

        self._process_contracts(slither.contracts)

    def _process_contracts(self, contracts):
        for contract in contracts:
            for function in contract.functions:
                self._process_function(contract, function)

    def _process_function(self, contract, function):
        self.contract_functions[contract].add(
            _node(_function_node(contract, function), function.name),
        )

        for internal_call in function.internal_calls:
            self._process_internal_call(contract, function, internal_call)
        for external_call in function.high_level_calls:
            self._process_external_call(contract, function, external_call)

    def _process_internal_call(self, contract, function, internal_call):
        if isinstance(internal_call, (Function)):
            self.contract_calls[contract].add(_edge(
                _function_node(contract, function),
                _function_node(contract, internal_call),
            ))
        elif isinstance(internal_call, (SolidityFunction)):
            self.solidity_functions.add(
                _node(_solidity_function_node(internal_call)),
            )
            self.solidity_calls.add(_edge(
                _function_node(contract, function),
                _solidity_function_node(internal_call),
            ))

    def _process_external_call(self, contract, function, external_call):
        external_contract, external_function = external_call

        # add variable as node to respective contract
        if isinstance(external_function, (Variable)):
            self.contract_functions[external_contract].add(_node(
                _function_node(external_contract, external_function),
                external_function.name
            ))

        self.external_calls.add(_edge(
            _function_node(contract, function),
            _function_node(external_contract, external_function),
        ))

    def _render_internal_calls(self):
        lines = []

        for contract in self.contract_functions:
            lines.append(f'subgraph {_contract_subgraph(contract)} {{')
            lines.append(f'label = "{contract.name}"')

            lines.extend(self.contract_functions[contract])
            lines.extend(self.contract_calls[contract])

            lines.append('}')

        return '\n'.join(lines)

    def _render_solidity_calls(self):
        lines = []

        lines.append('subgraph cluster_solidity {')
        lines.append('label = "[Solidity]"')

        lines.extend(self.solidity_functions)
        lines.extend(self.solidity_calls)

        lines.append('}')

        return '\n'.join(lines)

    def _render_external_calls(self):
        return '\n'.join(self.external_calls)

    def output(self, filename):
        """
            Output the graph in filename
            Args:
                filename(string)
        """
        if not filename.endswith('.dot'):
            filename += '.dot'

        self.info(f'Call Graph: {filename}')

        with open(filename, 'w') as f:
            f.write('\n'.join([
                'strict digraph {',
                self._render_internal_calls(),
                self._render_solidity_calls(),
                self._render_external_calls(),
                '}',
            ]))
