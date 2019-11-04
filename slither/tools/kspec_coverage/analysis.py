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
    results = []

    # Loop for each underlying contract
    for contract in slither.contracts:
        if not include_interfaces and contract.is_signature_only():
            continue
        functions_to_search = []
        functions_to_search += contract.functions_declared
        if include_modifiers:
            functions_to_search += contract.modifiers
        # Loop for each function
        for function in functions_to_search:
            if function.is_constructor or (not include_interfaces and function.is_empty is not False):
                continue
            results.append((contract, function))

        # Loop for each state variable to account for getters
        for variable in contract.variables:
            if variable.visibility not in ['public', 'external']:
                continue
            results.append((contract, variable))
                
    return results


def _add_current_row(count_kspec_direct, count_kspec_missing,
                     current_kspec_direct, current_kspec_missing, previous_contract, rows):
    desc_column = "{}".format(previous_contract)
    rows.append([desc_column,
                 '\n'.join(current_kspec_direct),
                 '\n'.join(current_kspec_missing)])
    count_kspec_direct += len(current_kspec_direct)
    count_kspec_missing += len(current_kspec_missing)

def _run_coverage_analysis(slither, kspec_functions, consider_derived=True):
    # Collect all slither functions
    slither_functions = _get_slither_functions(slither)
    slither_functions = {(contract.name, function.full_name): function for (contract, function) in slither_functions}

    # Determine which klab specs were not resolved.
    slither_functions_set = set(slither_functions)
    kspec_functions_resolved = kspec_functions & slither_functions_set
    kspec_functions_unresolved = kspec_functions - kspec_functions_resolved

    # Print out messages regarding covered functions
    previous_contract = None
    header_row = ['Contract Name', 'kspec funcs', 'not covered funcs']
    rows = []
    current_kspec_direct, current_kspec_missing = ([], [])
    count_kspec_direct, count_kspec_missing = (0, 0)

    for slither_func_desc in sorted(slither_functions_set):
        slither_func = slither_functions[slither_func_desc]
        if not isinstance(slither_func, Function) or slither_func.contract_declarer.name != slither_func_desc[0]:
            continue

        # If we are now describing a new contract, append our previous row and clear our current function info.
        if slither_func_desc[0] != previous_contract:
            if previous_contract is not None:
                _add_current_row(count_kspec_direct, count_kspec_missing,
                                 current_kspec_direct, current_kspec_missing, previous_contract, rows)

            previous_contract = slither_func_desc[0]
            current_kspec_direct = []
            current_kspec_missing = []

        # Determine which column to add the function to
        if slither_func_desc in kspec_functions:
            current_kspec_direct.append(slither_func_desc[1])
        else:
            current_kspec_missing.append(slither_func_desc[1])

    # Add our last constructed row
    if previous_contract is not None:
        _add_current_row(count_kspec_direct, count_kspec_missing,
                         current_kspec_direct, current_kspec_missing, previous_contract, rows)

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

