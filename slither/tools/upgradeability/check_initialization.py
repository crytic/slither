import logging

from slither.slithir.operations import InternalCall
from slither.utils import json_utils
from slither.utils.colors import red, yellow, green

logger = logging.getLogger("Slither-check-upgradeability")

class MultipleInitTarget(Exception):
    pass

def _get_initialize_functions(contract):
    return [f for f in contract.functions if f.name == 'initialize' and f.is_implemented]

def _get_all_internal_calls(function):
    all_ir = function.all_slithir_operations()
    return [i.function for i in all_ir if isinstance(i, InternalCall) and i.function_name == "initialize"]


def _get_most_derived_init(contract):
    init_functions = [f for f in contract.functions if not f.is_shadowed and f.name == 'initialize']
    if len(init_functions) > 1:
        if len([f for f in init_functions if f.contract_declarer == contract]) == 1:
            return next((f for f in init_functions if f.contract_declarer == contract))
        raise MultipleInitTarget
    if init_functions:
        return init_functions[0]
    return None

def check_initialization(contract):

    results = {
        'Initializable-present': False,
        'Initializable-inherited': False,
        'Initializable.initializer()-present': False,
        'missing-initializer-modifier': [],
        'initialize_target': {},
        'missing-calls': [],
        'multiple-calls': []
    }

    error_found = False

    logger.info(green(
        '\n## Run initialization checks... (see https://github.com/crytic/slither/wiki/Upgradeability-Checks#initialization-checks)'))

    # Check if the Initializable contract is present
    initializable = contract.slither.get_contract_from_name('Initializable')
    if initializable is None:
        logger.info(yellow('Initializable contract not found, the contract does not follow a standard initalization schema.'))
        return results
    results['Initializable-present'] = True

    # Check if the Initializable contract is inherited
    if initializable not in contract.inheritance:
        logger.info(
            yellow('The logic contract does not call the initializer.'))
        return results
    results['Initializable-inherited'] = True

    # Check if the Initializable contract is inherited
    initializer = contract.get_modifier_from_canonical_name('Initializable.initializer()')
    if initializer is None:
        logger.info(
            yellow('Initializable.initializer() does not exist'))
        return results
    results['Initializable.initializer()-present'] = True

    # Check if a init function lacks the initializer modifier
    initializer_modifier_missing = False
    all_init_functions = _get_initialize_functions(contract)
    for f in all_init_functions:
        if not initializer in f.modifiers:
            initializer_modifier_missing = True
            info = f'{f.canonical_name} does not call the initializer modifier'
            logger.info(red(info))
            json_elem = json_utils.generate_json_result(info)
            json_utils.add_function_to_json(f, json_elem)
            results['missing-initializer-modifier'].append(json_elem)

    if not initializer_modifier_missing:
        logger.info(green('All the init functions have the initializer modifier'))

    # Check if we can determine the initialize function that will be called
    # TODO: handle MultipleInitTarget
    try:
        most_derived_init = _get_most_derived_init(contract)
    except MultipleInitTarget:
        logger.info(red('Too many init targets'))
        return results

    if most_derived_init is None:
        init_info = f'{contract.name} has no initialize function\n'
        logger.info(green(init_info))
        results['initialize_target'] = {}
        return results
    # results['initialize_target'] is set at the end, as we want to print it last

    # Check if an initialize function is not called from the most_derived_init function
    missing_call = False
    all_init_functions_called = _get_all_internal_calls(most_derived_init) + [most_derived_init]
    missing_calls = [f for f in all_init_functions if not f in all_init_functions_called]
    for f in missing_calls:
        info = f'Missing call to {f.canonical_name} in {most_derived_init.canonical_name}'
        logger.info(red(info))
        json_elem = json_utils.generate_json_result(info)
        json_utils.add_function_to_json(f, json_elem, {"is_most_derived_init_function": False})
        json_utils.add_function_to_json(most_derived_init, json_elem, {"is_most_derived_init_function": True})
        results['missing-calls'].append(json_elem)
        missing_call = True
    if not missing_call:
        logger.info(green('No missing call to an init function found'))

    # Check if an init function is called multiple times
    double_calls = list(set([f for f in all_init_functions_called if all_init_functions_called.count(f) > 1]))
    double_calls_found = False
    for f in double_calls:
        info = f'{f.canonical_name} is called multiple times in {most_derived_init.full_name}'
        logger.info(red(info))
        json_elem = json_utils.generate_json_result(info)
        json_utils.add_function_to_json(f, json_elem)
        results['multiple-calls'].append(json_elem)
        double_calls_found = True
    if not double_calls_found:
        logger.info(green('No double call to init functions found'))

    # Print the initialize_target info

    init_info = f'{contract.name} needs to be initialized by {most_derived_init.full_name}\n'
    logger.info(green('Check the deployement script to ensure that these functions are called:\n' + init_info))
    json_elem = json_utils.generate_json_result(init_info)
    json_utils.add_function_to_json(most_derived_init, json_elem)
    results['initialize_target'] = json_elem

    if not error_found:
        logger.info(green('No error found'))

    return results
