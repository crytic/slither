import re
import logging
from slither.solc_parsing.declarations.function import Function
from slither.utils import json_utils

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


def _run_coverage_analysis(args, slither, kspec_functions, consider_derived=True):
    # Collect all slither functions
    slither_functions = _get_slither_functions(slither)
    slither_functions = {(contract.name, function.full_name): function for (contract, function) in slither_functions}

    # Determine which klab specs were not resolved.
    slither_functions_set = set(slither_functions)
    kspec_functions_resolved = kspec_functions & slither_functions_set
    kspec_functions_unresolved = kspec_functions - kspec_functions_resolved

    kspec_missing = []
    kspec_present = []

    for slither_func_desc in sorted(slither_functions_set):
        slither_func = slither_functions[slither_func_desc]
        if not isinstance(slither_func, Function) or slither_func.contract_declarer.name != slither_func_desc[0]:
            continue
        if slither_func_desc in kspec_functions:
            kspec_present.append(slither_func)
        else:
            kspec_missing.append(slither_func)

    json_kspec_present = json_utils.generate_json_result("Functions with kspec present")
    for function in kspec_present:
        if args.json:
            json_utils.add_function_to_json(function, json_kspec_present)
        else:
            logger.info(f"kspec present for {function.contract.name}.{function.full_name}")            

    json_kspec_missing = json_utils.generate_json_result("Functions with kspec missing")
    for function in kspec_missing:
        if args.json:
            json_utils.add_function_to_json(function, json_kspec_missing)
        else:
            logger.warning(f"kspec missing for {function.contract.name}.{function.full_name}")
    
    # Handle unresolved kspecs
    if args.json:
        kspec_functions_unresolved_str = ', '.join(str(e) for e in list(kspec_functions_unresolved))
        json_kspec_unresolved = json_utils.generate_json_result("Kspec unresolved functions " +
                                                                kspec_functions_unresolved_str)
    else:
        for contract_name, function_name in sorted(kspec_functions_unresolved):
            logger.warning(f"Could not find function for klab spec:{contract_name}.{function_name}")

    if args.json:
        json_utils.output_json(args.json, None,
                               {
                                   "kspec_present": json_kspec_present,
                                   "kspec_missing": json_kspec_missing,
                                   "kspec_unresolved": json_kspec_unresolved
                               })
                
def run_analysis(args, slither, kspec):
    # Get all of our kspec'd functions (tuple(contract_name, function_name)).
    kspec_functions = _get_all_covered_kspec_functions(kspec)

    # Run coverage analysis
    _run_coverage_analysis(args, slither, kspec_functions)

