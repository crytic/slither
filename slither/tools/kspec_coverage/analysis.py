import re
import logging
from slither.utils.colors import yellow, green, red
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


def _get_slither_functions(slither):
    # Use contract == contract_declarer to avoid dupplicate
    all_functions_declared = [f for f in slither.functions if (f.contract == f.contract_declarer
                                                               and not f.is_constructor
                                                               and not f.is_empty
                                                               and not f.is_constructor_variables)]
    # Use list(set()) because same state variable instances can be shared accross contracts
    # TODO: integrate state variables
    # all_functions_declared += list(set([s for s in slither.state_variables if s.visibility in ['public', 'external']]))
    #
    slither_functions = {(function.contract.name, function.full_name): function for function in all_functions_declared}
                
    return slither_functions

def _generate_output(kspec, message, color, generate_json):
    info = ""
    for function in kspec:
        info += f"{message} {function.contract.name}.{function.full_name}"
    if info:
        logger.info(color(info))

    if generate_json:
        json_kspec_present = json_utils.generate_json_result(info)
        for function in kspec:
            json_utils.add_function_to_json(function, json_kspec_present)
        return json_kspec_present
    return None

def _generate_output_unresolved(kspec, message, color, generate_json):
    info = ""
    for contract, function in kspec:
        info += f"{message} {contract}.{function}"
    if info:
        logger.info(color(info))

    if generate_json:
        json_kspec_present = json_utils.generate_json_result(info, additional_fields={"signatures": kspec})
        return json_kspec_present
    return None



def _run_coverage_analysis(args, slither, kspec_functions):
    # Collect all slither functions
    slither_functions = _get_slither_functions(slither)

    # Determine which klab specs were not resolved.
    slither_functions_set = set(slither_functions)
    kspec_functions_resolved = kspec_functions & slither_functions_set
    kspec_functions_unresolved = kspec_functions - kspec_functions_resolved


    kspec_missing = []
    kspec_present = []

    for slither_func_desc in sorted(slither_functions_set):
        slither_func = slither_functions[slither_func_desc]

        if slither_func_desc in kspec_functions:
            kspec_present.append(slither_func)
        else:
            kspec_missing.append(slither_func)

    logger.info('## Check for functions coverage')
    json_kspec_present = _generate_output(kspec_present, "[✓]", green, args.json)
    json_kspec_missing = _generate_output(kspec_missing, "[ ] (Missing)", red, args.json)
    json_kspec_unresolved = _generate_output_unresolved(kspec_functions_unresolved,
                                                        "[ ] (Unresolved)",
                                                        yellow,
                                                        args.json)
    
    # Handle unresolved kspecs
    if args.json:
        json_utils.output_json(args.json, None, {
                                   "kspec_present": json_kspec_present,
                                   "kspec_missing": json_kspec_missing,
                                   "kspec_unresolved": json_kspec_unresolved
                               })
                
def run_analysis(args, slither, kspec):
    # Get all of our kspec'd functions (tuple(contract_name, function_name)).
    kspec_functions = _get_all_covered_kspec_functions(kspec)

    # Run coverage analysis
    _run_coverage_analysis(args, slither, kspec_functions)

