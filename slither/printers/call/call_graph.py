"""
    Module printing the call graph

    The call graph shows for each function,
    what are the contracts/functions called.
    The output is a dot file named filename.dot
"""
from collections import defaultdict
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
    HELP = 'Export the call-graph of the contracts to a dot file'

    WIKI = 'https://github.com/trailofbits/slither/wiki/Printer-documentation#call-graph'

    def _process_functions(self, functions):

        contract_functions = defaultdict(set) # contract -> contract functions nodes
        contract_calls = defaultdict(set) # contract -> contract calls edges

        solidity_functions = set() # solidity function nodes
        solidity_calls = set() # solidity calls edges
        external_calls = set() # external calls edges

        all_contracts = set()

        for function in functions:
            all_contracts.add(function.contract)
        for function in functions:
            self._process_function(function.contract,
                                   function,
                                   contract_functions,
                                   contract_calls,
                                   solidity_functions,
                                   solidity_calls,
                                   external_calls,
                                   all_contracts)

        render_internal_calls = ''
        for contract in all_contracts:
            render_internal_calls += self._render_internal_calls(contract, contract_functions, contract_calls)

        render_solidity_calls = '' #self._render_solidity_calls(solidity_functions, solidity_calls)

        render_external_calls = self._render_external_calls(external_calls)

        return render_internal_calls + render_solidity_calls + render_external_calls

    def _process_function(self, contract, function, contract_functions, contract_calls, solidity_functions, solidity_calls, external_calls, all_contracts):
        contract_functions[contract].add(
            _node(_function_node(contract, function), function.name),
        )

        for internal_call in function.internal_calls:
            self._process_internal_call(contract, function, internal_call, contract_calls, solidity_functions, solidity_calls)
        for external_call in function.high_level_calls:
            self._process_external_call(contract, function, external_call, contract_functions, external_calls, all_contracts)

    def _process_internal_call(self, contract, function, internal_call, contract_calls, solidity_functions, solidity_calls):
        if isinstance(internal_call, (Function)):
            contract_calls[contract].add(_edge(
                _function_node(contract, function),
                _function_node(contract, internal_call),
            ))
        elif isinstance(internal_call, (SolidityFunction)):
            solidity_functions.add(
                _node(_solidity_function_node(internal_call)),
            )
            solidity_calls.add(_edge(
                _function_node(contract, function),
                _solidity_function_node(internal_call),
            ))

    def _process_external_call(self, contract, function, external_call, contract_functions, external_calls, all_contracts):
        external_contract, external_function = external_call

        if not external_contract in all_contracts:
            return

        # add variable as node to respective contract
        if isinstance(external_function, (Variable)):
            return
            contract_functions[external_contract].add(_node(
                _function_node(external_contract, external_function),
                external_function.name
            ))

        external_calls.add(_edge(
            _function_node(contract, function),
            _function_node(external_contract, external_function),
        ))

    def _render_internal_calls(self, contract, contract_functions, contract_calls):
        lines = []

        lines.append(f'subgraph {_contract_subgraph(contract)} {{')
        lines.append(f'label = "{contract.name}"')

        lines.extend(contract_functions[contract])
        lines.extend(contract_calls[contract])

        lines.append('}')

        return '\n'.join(lines)

    def _render_solidity_calls(self, solidity_functions, solidity_calls):
        lines = []

        lines.append('subgraph cluster_solidity {')
        lines.append('label = "[Solidity]"')

        lines.extend(solidity_functions)
        lines.extend(solidity_calls)

        lines.append('}')

        return '\n'.join(lines)

    def _render_external_calls(self, external_calls):
        return '\n'.join(external_calls)



    def output(self, filename):
        """
            Output the graph in filename
            Args:
                filename(string)
        """

        if not filename.endswith('.dot'):
            filename += '.dot'
        if filename == ".dot":
            filename = "all_contracts.dot"

        with open(filename, 'w', encoding='utf8') as f:
            self.info(f'Call Graph: {filename}')
            f.write('\n'.join(['strict digraph {'] + [self._process_functions(self.slither.functions)] +  ['}']))


        for derived_contract in self.slither.contracts_derived:
            with open(f'{derived_contract.name}.dot', 'w', encoding='utf8') as f:
                self.info(f'Call Graph: {derived_contract.name}.dot')
                f.write('\n'.join(['strict digraph {'] + [self._process_functions(derived_contract.functions)] +  ['}']))

