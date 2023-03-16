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
def _function_node(function, top_level_dict):
    if isinstance(function, (FunctionTopLevel)):
        return f"{top_level_dict[function].id}_{function.name}"
    return f"{function.contract_declarer.id}_{function.name}"


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


# pylint: disable=too-few-public-methods
class DummyContractForTopLevel:
    """Dummy Class to simulate Contract Declarer for top level functions"""

    def __init__(self, identifier, name):
        self.id = identifier
        self.name = name


# pylint: disable=too-many-arguments
def _process_internal_call(
    contract,
    function,
    internal_call,
    contract_calls,
    solidity_functions,
    solidity_calls,
    top_level_dict,
):
    if isinstance(internal_call, (FunctionTopLevel)):
        contract_calls[contract].add(
            _edge(
                _function_node(function, top_level_dict),
                _function_node(internal_call, top_level_dict),
            )
        )
    elif isinstance(internal_call, (Function)):
        contract_calls[contract].add(
            _edge(
                _function_node(function, top_level_dict),
                _function_node(internal_call, top_level_dict),
            )
        )
    elif isinstance(internal_call, (SolidityFunction)):
        solidity_functions.add(
            _node(_solidity_function_node(internal_call)),
        )
        solidity_calls.add(
            _edge(
                _function_node(function, top_level_dict),
                _solidity_function_node(internal_call),
            )
        )


def _render_external_calls(external_calls):
    external_calls_sorted = sorted(external_calls)
    return "\n".join(external_calls_sorted)


def _render_internal_nodes(contract, contract_functions):
    lines = []

    lines.append(f"subgraph {_contract_subgraph(contract)} {{")
    lines.append(f'label = "{contract.name}"')
    contract_functions_sorted = sorted(contract_functions[contract])
    lines.extend(contract_functions_sorted)

    lines.append("}")

    return "\n".join(lines)


def _render_internal_edges(contract, contract_calls):
    lines = []
    contract_calls_sorted = sorted(contract_calls[contract])
    lines.extend(contract_calls_sorted)
    return "\n".join(lines)


def _render_solidity_nodes(solidity_functions):
    lines = []
    lines.append("subgraph cluster_solidity {")
    lines.append('label = "[Solidity]"')
    solidity_functions_sorted = sorted(solidity_functions)
    lines.extend(solidity_functions_sorted)

    lines.append("}")

    return "\n".join(lines)


def _render_solidity_edges(solidity_calls):
    lines = []
    solidity_calls_sorted = sorted(solidity_calls)
    lines.extend(solidity_calls_sorted)
    return "\n".join(lines)


def _process_external_call(
    function,
    external_call,
    contract_functions,
    external_calls,
    all_contracts,
    top_level_dict,
):
    external_contract, external_function = external_call

    if not external_contract in all_contracts:
        return

    # add variable as node to respective contract
    if isinstance(external_function, (Variable)):
        contract_functions[external_contract].add(
            _node(
                _function_node(external_function, top_level_dict),
                external_function.name,
            )
        )
    # Todo: probably unreachable since top level functions are internal
    if isinstance(external_function, (FunctionTopLevel)):
        external_calls.add(
            _edge(
                _function_node(function, top_level_dict),
                _function_node(external_function, top_level_dict),
            )
        )
    else:
        external_calls.add(
            _edge(
                _function_node(function, top_level_dict),
                _function_node(external_function, top_level_dict),
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
    top_level_dict,
):
    contract_functions[contract].add(
        _node(_function_node(function, top_level_dict), function.name),
    )

    for internal_call in function.internal_calls:

        _process_internal_call(
            contract,
            function,
            internal_call,
            contract_calls,
            solidity_functions,
            solidity_calls,
            top_level_dict,
        )
    for external_call in function.high_level_calls:

        _process_external_call(
            function,
            external_call,
            contract_functions,
            external_calls,
            all_contracts,
            top_level_dict,
        )


def _create_dummy_declarers(top_level_functions):
    if top_level_functions == []:
        return None

    my_filenames = []
    sorted_by_filename = sorted(top_level_functions, key=lambda x: x.source_mapping.filename)
    current_filename = sorted_by_filename[0].source_mapping.filename.absolute

    formatted_name = current_filename[current_filename.rfind("/") + 1 : current_filename.rfind(".")]
    current_declarer = DummyContractForTopLevel(
        f"TopLevelFunctions_{formatted_name}", f"TopLevel_{formatted_name}"
    )
    function_to_contract = {}
    for fn in sorted_by_filename:
        if fn.source_mapping.filename in my_filenames:
            function_to_contract[fn] = current_declarer
        else:
            current_filename = fn.source_mapping.filename.absolute
            formatted_name = current_filename[
                current_filename.rfind("/") + 1 : current_filename.rfind(".")
            ]
            current_declarer = DummyContractForTopLevel(
                f"TopLevelFunctions_{formatted_name}", f"TopLevel_{formatted_name}"
            )
            function_to_contract[fn] = current_declarer
            my_filenames.append(fn.source_mapping.filename)

    return function_to_contract


# pylint: disable=too-many-locals
def _process_functions(functions, top_level_dict):
    contract_functions = defaultdict(set)  # contract -> contract functions nodes
    contract_calls = defaultdict(set)  # contract -> contract calls edges
    solidity_functions = set()  # solidity function nodes
    solidity_calls = set()  # solidity calls edges
    external_calls = set()  # external calls edges
    all_contracts = set()
    # We have to loop twice, because external functions require all_contracts to be fully populated
    for function in functions:
        all_contracts.add(function.contract_declarer)

    for function in functions:
        _process_function(
            function.contract_declarer,
            function,
            contract_functions,
            contract_calls,
            solidity_functions,
            solidity_calls,
            external_calls,
            all_contracts,
            top_level_dict,
        )
    if top_level_dict is not None:
        # todo: since top level functions are internal, we might be able to just loop once here
        for top_level in top_level_dict.keys():
            all_contracts.add(top_level_dict[top_level])
        for top_level in top_level_dict.keys():
            _process_function(
                top_level_dict[top_level],
                top_level,
                contract_functions,
                contract_calls,
                solidity_functions,
                solidity_calls,
                external_calls,
                all_contracts,
                top_level_dict,
            )
    render_internal_nodes = ""
    render_internal_edges = ""
    all_contracts_sorted = sorted(all_contracts, key=lambda x:x.name)
    for contract in all_contracts_sorted:
        render_internal_nodes += _render_internal_nodes(contract, contract_functions)
        render_internal_edges += _render_internal_edges(contract, contract_calls)

    render_solidity_nodes = _render_solidity_nodes(solidity_functions)

    render_external_calls = _render_external_calls(external_calls)

    render_solidity_edges = _render_solidity_edges(solidity_calls)

    return (
        render_internal_nodes
        + render_solidity_nodes
        + render_external_calls
        + render_internal_edges
        + render_solidity_edges
    )


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
            compilation_units = self.slither.compilation_units
            functions_to_investigate, top_level_dict = _setup_functions(compilation_units)
            content = "\n".join(
                ["strict digraph {"]
                + [_process_functions(functions_to_investigate, top_level_dict)]
                + ["}"]
            )
            f.write(content)
            results.append((all_contracts_filename, content))

        for derived_contract in self.slither.contracts_derived:
            derived_output_filename = f"{filename}{derived_contract.name}.call-graph.dot"

            with open(derived_output_filename, "w", encoding="utf8") as f:
                info += f"Call Graph: {derived_output_filename}\n"
                content = "\n".join(
                    ["strict digraph {"]
                    + [_process_functions(derived_contract.functions, top_level_dict)]
                    + ["}"]
                )
                f.write(content)
                results.append((derived_output_filename, content))

        self.info(info)
        res = self.generate_output(info)
        for filename_result, content in results:
            res.add_file(filename_result, content)

        return res


def _setup_functions(slither_compilation_units):
    # Avoid duplicate functions due to different compilation unit
    all_functionss = [compilation_unit.functions for compilation_unit in slither_compilation_units]
    all_functions = [item for sublist in all_functionss for item in sublist]
    top_levels = [
        compilation_unit.functions_top_level for compilation_unit in slither_compilation_units
    ]
    top_levels_flat = [item for sublist in top_levels for item in sublist]
    top_level_dict = _create_dummy_declarers(top_levels_flat)
    if top_level_dict is not None:
        all_functions_as_dict = {
            function.canonical_name: function
            for function in all_functions
            if function not in top_level_dict
        }
    else:
        all_functions_as_dict = {function.canonical_name: function for function in all_functions}
    return (all_functions_as_dict.values(), top_level_dict)
