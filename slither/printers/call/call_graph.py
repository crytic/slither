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
from slither.core.declarations.function_top_level import FunctionTopLevel
from slither.core.variables.variable import Variable


def _contract_subgraph(contract):
    return f"cluster_{contract.id}_{contract.name}"


# return unique id for contract function to use as node name
def _function_node(contract, function):
    return f"{contract.id}_{function.name}"


# return unique id for solidity function to use as node name
def _solidity_function_node(solidity_function):
    return f"{solidity_function.name}"


# return dot language string to add graph edge
def _edge(from_node, to_node):
    return f'"{from_node}" -> "{to_node}"'


# return dot language string to add graph node (with optional label)
def _node(node, label=None):
    return " ".join(
        (
            f'"{node}"',
            f'[label="{label}"]' if label is not None else "",
        )
    )

#pylint: disable=too-few-public-methods
class DummyContractForTopLevel:
    """Dummy Class to simulate Contract Declarer for top level functions"""
    def __init__(self,identifier,name):
        self.id = identifier
        self.name = name

d = DummyContractForTopLevel("TopLevelFunction","toplevel")

# pylint: disable=too-many-arguments
def _process_internal_call(
    contract,
    function,
    internal_call,
    contract_calls,
    solidity_functions,
    solidity_calls,
):
    if isinstance(internal_call,(FunctionTopLevel)):
        contract_calls[contract].add(
            _edge(
                _function_node(contract,function),
                _function_node(d,internal_call),
            )
        )
    elif isinstance(internal_call, (Function)):
        contract_calls[contract].add(
            _edge(
                _function_node(contract, function),
                _function_node(contract, internal_call),
            )
        )
    elif isinstance(internal_call, (SolidityFunction)):
        solidity_functions.add(
            _node(_solidity_function_node(internal_call)),
        )
        solidity_calls.add(
            _edge(
                _function_node(contract, function),
                _solidity_function_node(internal_call),
            )
        )


def _render_external_calls(external_calls):
    return "\n".join(external_calls)


def _render_internal_nodes(contract, contract_functions):
    lines = []

    lines.append(f"subgraph {_contract_subgraph(contract)} {{")
    lines.append(f'label = "{contract.name}"')

    lines.extend(contract_functions[contract])

    lines.append("}")

    return "\n".join(lines)

def _render_internal_edges(contract,contract_calls):
    lines = []
    lines.extend(contract_calls[contract])
    return "\n".join(lines)


def _render_solidity_nodes(solidity_functions):
    lines = []
    lines.append("subgraph cluster_solidity {")
    lines.append('label = "[Solidity]"')

    lines.extend(solidity_functions)

    lines.append("}")

    return "\n".join(lines)

def _render_solidity_edges(solidity_calls):
    lines = []
    lines.extend(solidity_calls)
    return "\n".join(lines)


def _process_external_call(
    contract,
    function,
    external_call,
    contract_functions,
    external_calls,
    all_contracts,
):
    external_contract, external_function = external_call

    if not external_contract in all_contracts:
        return

    # add variable as node to respective contract
    if isinstance(external_function, (Variable)):
        contract_functions[external_contract].add(
            _node(
                _function_node(external_contract, external_function),
                external_function.name,
            )
        )

    external_calls.add(
        _edge(
            _function_node(contract, function),
            _function_node(external_contract, external_function),
        )
    )


# pylint: disable=too-many-arguments
def _process_function(
    contract,
    function,
    contract_functions,
    contract_calls,
    solidity_functions,
    solidity_calls,
    external_calls,
    all_contracts,
):
    contract_functions[contract].add(
        _node(_function_node(contract, function), function.name),
    )

    for internal_call in function.internal_calls:
        _process_internal_call(
            contract,
            function,
            internal_call,
            contract_calls,
            solidity_functions,
            solidity_calls,
        )
    for external_call in function.high_level_calls:
        _process_external_call(
            contract,
            function,
            external_call,
            contract_functions,
            external_calls,
            all_contracts,
        )

#Todo: grab top level functions by common source map
# Make contracts with the same source file declaration be in the same contract declarer
# Deal with the inlined functions

def _process_functions(functions):
    contract_functions = defaultdict(set)  # contract -> contract functions nodes
    contract_calls = defaultdict(set)  # contract -> contract calls edges

    solidity_functions = set()  # solidity function nodes
    solidity_calls = set()  # solidity calls edges
    external_calls = set()  # external calls edges

    all_contracts = set()


    for function in functions:
        if isinstance(function,(FunctionTopLevel)):

            all_contracts.add(d)
        else:
            all_contracts.add(function.contract_declarer)

    for function in functions:
        if isinstance(function,(FunctionTopLevel)):
            _process_function(
                d,
                function,
                contract_functions,
                contract_calls,
                solidity_functions,
                solidity_calls,
                external_calls,
                all_contracts,
            )
        else:
            _process_function(
                function.contract_declarer,
                function,
                contract_functions,
                contract_calls,
                solidity_functions,
                solidity_calls,
                external_calls,
                all_contracts,
            )

    render_internal_nodes = ""
    render_internal_edges = ""
    for contract in all_contracts:
        render_internal_nodes += _render_internal_nodes(
            contract, contract_functions
        )
        render_internal_edges += _render_internal_edges(contract,contract_calls)

    render_solidity_nodes = _render_solidity_nodes(solidity_functions)

    render_external_calls = _render_external_calls(external_calls)

    render_solidity_edges = _render_solidity_edges(solidity_calls)

    return render_internal_nodes + render_solidity_nodes + render_external_calls + render_internal_edges + render_solidity_edges


class PrinterCallGraph(AbstractPrinter):
    ARGUMENT = "call-graph"
    HELP = "Export the call-graph of the contracts to a dot file"

    WIKI = "https://github.com/trailofbits/slither/wiki/Printer-documentation#call-graph"

    def output(self, filename):
        """
        Output the graph in filename
        Args:
            filename(string)
        """

        all_contracts_filename = ""
        if not filename.endswith(".dot"):
            if filename in ("", "."):
                filename = ""
            else:
                filename += "."
            all_contracts_filename = f"{filename}all_contracts.call-graph.dot"

        if filename == ".dot":
            all_contracts_filename = "all_contracts.dot"

        info = ""
        results = []
        with open(all_contracts_filename, "w", encoding="utf8") as f:
            info += f"Call Graph: {all_contracts_filename}\n"

            # Avoid duplicate functions due to different compilation unit
            all_functionss = [
                compilation_unit.functions for compilation_unit in self.slither.compilation_units
            ]
            all_functions = [item for sublist in all_functionss for item in sublist]
            all_functions_as_dict = {
                function.canonical_name: function for function in all_functions
            }
            content = "\n".join(
                ["strict digraph {"] + [_process_functions(all_functions_as_dict.values())] + ["}"]
            )
            f.write(content)
            results.append((all_contracts_filename, content))
        for derived_contract in self.slither.contracts_derived:
            derived_output_filename = f"{filename}{derived_contract.name}.call-graph.dot"
            with open(derived_output_filename, "w", encoding="utf8") as f:
                info += f"Call Graph: {derived_output_filename}\n"
                content = "\n".join(
                    ["strict digraph {"] + [_process_functions(derived_contract.functions)] + ["}"]
                )
                f.write(content)
                results.append((derived_output_filename, content))

        self.info(info)
        res = self.generate_output(info)
        for filename_result, content in results:
            res.add_file(filename_result, content)

        return res