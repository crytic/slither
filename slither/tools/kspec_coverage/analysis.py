import re
import logging
from math import sqrt
from slither.core.solidity_types.user_defined_type import UserDefinedType
from slither.solc_parsing.declarations.function import Function
from slither.core.declarations.solidity_variables import SolidityFunction
from tabulate import tabulate

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger('Slither.kspec')

def _refactor_type(type):
    return {
        'uint': 'uint256',
        'int': 'int256'
    }.get(type, type)

def _get_all_covered_kspec_functions(target):
    # Create a set of our discovered functions which are covered
    covered_functions = set()

    BEHAVIOUR_PATTERN = re.compile('behaviour\s+(\S+)\s+of\s+(\S+)')
    INTERFACE_PATTERN = re.compile('interface\s+([^\r\n]+)')

    # Read the file contents
    with open(target, 'r', encoding='utf8') as target_file:
        lines = target_file.readlines()

    # Loop for each line, if a line matches our behaviour regex, and the next one matches our interface regex,
    # we add our finding
    i = 0
    while i < len(lines):
        match = BEHAVIOUR_PATTERN.match(lines[i])
        if match:
            contract_name = match.groups()[1]
            match = INTERFACE_PATTERN.match(lines[i + 1])
            if match:
                function_full_name = match.groups()[0]
                start, end = function_full_name.index('(') + 1, function_full_name.index(')')
                function_arguments = function_full_name[start:end].split(',')
                function_arguments = [_refactor_type(arg.strip().split(' ')[0]) for arg in function_arguments]
                function_full_name = function_full_name[:start] + ','.join(function_arguments) + ')'
                covered_functions.add((contract_name, function_full_name))
                i += 1
        i += 1
    return covered_functions


def _get_slither_functions(slither, include_modifiers=False, include_interfaces=False):
    # Loop for each compilation's underlying contracts
    results = []

    # Loop for each underlying contract
    for contract in slither.contracts:
        if not include_interfaces and contract.is_signature_only():
            continue
        # Loop for each function
        functions_to_search = []
        functions_to_search += contract.functions_declared
        if include_modifiers:
            functions_to_search += contract.modifiers
        for function in functions_to_search:
            if function.is_constructor or (not include_interfaces and function.is_empty is not False):
                continue
            results.append((contract, function))

        # Loop for each state variable
        for variable in contract.variables:
            if variable.visibility not in ['public', 'external']:
                continue
            results.append((contract, variable))

    return results


def _get_functions_reached(compiled_functions, origin_func_desc, results):

    # If this function is already in the set, stop
    if origin_func_desc in results:
        return

    # Add this function to the results
    results.add(origin_func_desc)

    # Find all functions with this signature.
    origin_funcs = [(contract, function)
                    for (contract, function) in compiled_functions
                    if (contract.name, function.full_name) == origin_func_desc]

    # Process every function recursively.
    for (origin_contract, origin_function) in origin_funcs:
        # If this is not an actual function (possibly variable getter), stop
        if not isinstance(origin_function, Function):
            return

        # Find all function calls in this function (except for low level)
        called_functions = [f for (_, f) in origin_function.high_level_calls + origin_function.library_calls
                            if isinstance(f, Function)]
        called_functions += origin_function.internal_calls

        # Find all calls in these called functions.
        for called_function in called_functions:
            if not isinstance(called_function, SolidityFunction):
                _get_functions_reached(compiled_functions,
                                       (called_function.contract_declarer.name, called_function.full_name),
                                       results)


def _add_current_row(covered_percentages, count_kspec_direct, count_kspec_indirect, count_kspec_missing,
                     current_kspec_direct, current_kspec_indirect, current_kspec_missing, previous_contract, rows):
    total_current_count = len(current_kspec_direct) + len(current_kspec_indirect) + len (current_kspec_missing)
    covered_percentage = 1 - (len(current_kspec_missing) / total_current_count)
    desc_column = "{} ({:.2%})".format(previous_contract, covered_percentage)
    rows.append([desc_column,
                 '\n'.join(current_kspec_direct),
                 '\n'.join(current_kspec_indirect),
                 '\n'.join(current_kspec_missing)])
    count_kspec_direct += len(current_kspec_direct)
    count_kspec_indirect += len(current_kspec_indirect)
    count_kspec_missing += len(current_kspec_missing)
    covered_percentages.append(covered_percentage)

def _run_coverage_analysis(slither, kspec_functions, consider_derived=True):
    # Collect all compiled functions
    compiled_functions = _get_slither_functions(slither)
    compiled_functions = {(contract.name, function.full_name): function for (contract, function) in compiled_functions}

    # Determine which klab specs were not resolved.
    compiled_functions_set = set(compiled_functions)
    kspec_functions_resolved = kspec_functions & compiled_functions_set
    kspec_functions_unresolved = kspec_functions - kspec_functions_resolved

    # Determine all functions that are touched by the resolved kspec functions
    kspec_functions_reached = set()
    all_available_functions = _get_slither_functions(slither, include_interfaces=True, include_modifiers=True)

    for func_desc in kspec_functions_resolved:
        _get_functions_reached(all_available_functions, func_desc, kspec_functions_reached)

    # Print out messages regarding covered functions
    covered_percentages = []
    previous_contract = None
    header_row = ['Contract Name', 'kspec funcs', 'kspec reached funcs', 'not covered funcs']
    rows = []
    current_kspec_direct, current_kspec_indirect, current_kspec_missing = ([], [], [])
    count_kspec_direct, count_kspec_indirect, count_kspec_missing = (0, 0, 0)

    for compiled_func_desc in sorted(compiled_functions_set):
        compiled_func = compiled_functions[compiled_func_desc]
        if not isinstance(compiled_func, Function) or compiled_func.contract_declarer.name != compiled_func_desc[0]:
            continue

        # If we are now describing a new contract, append our previous row and clear our current function info.
        if compiled_func_desc[0] != previous_contract:
            if previous_contract is not None:
                _add_current_row(covered_percentages, count_kspec_direct, count_kspec_indirect, count_kspec_missing,
                                 current_kspec_direct, current_kspec_indirect, current_kspec_missing, previous_contract, rows)

            previous_contract = compiled_func_desc[0]
            current_kspec_direct = []
            current_kspec_indirect = []
            current_kspec_missing = []

        # Determine which column to add the function to
        if compiled_func_desc in kspec_functions:
            current_kspec_direct.append(compiled_func_desc[1])
        elif compiled_func_desc in kspec_functions_reached:
            current_kspec_indirect.append(compiled_func_desc[1])
        else:
            current_kspec_missing.append(compiled_func_desc[1])

    # Add our last constructed row
    if previous_contract is not None:
        _add_current_row(covered_percentages, count_kspec_direct, count_kspec_indirect, count_kspec_missing,
                         current_kspec_direct, current_kspec_indirect, current_kspec_missing, previous_contract, rows)

    # Create our table and print it
    logger.info(tabulate(rows, header_row, tablefmt='grid'))

    # Print our message for unresolved kspecs
    if len(kspec_functions_unresolved) != 0:
        for contract_name, function_name in sorted(kspec_functions_unresolved):
            logger.info(f"Could not find function for klab spec:{contract_name}.{function_name}")
        logger.info(f"Could not find {len(kspec_functions_unresolved)}/{len(kspec_functions)}"
              f" functions referenced in klab spec")

def run_analysis(slither, kspec):
    # Get all of our kspec'd functions (tuple(contract_name, function_name)).
    kspec_functions = _get_all_covered_kspec_functions(kspec)

    # Run coverage analysis
    _run_coverage_analysis(slither, kspec_functions)

