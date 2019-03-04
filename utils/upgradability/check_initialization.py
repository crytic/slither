import logging
from slither import Slither
from slither.slithir.operations import InternalCall
from slither.utils.colors import green,red
from slither.utils.colors import red, yellow, green

logger = logging.getLogger("CheckInitialization")
logger.setLevel(logging.INFO)

class MultipleInitTarget(Exception):
    pass

def _get_initialize_functions(contract):
    return [f for father in contract.inheritance for f in father.functions_not_inherited if f.name == 'initialize']

def _get_all_internal_calls(function):
    all_ir = function.all_slithir_operations()
    return [i.function for i in all_ir if isinstance(i, InternalCall) and i.function_name == "initialize"]


def _get_most_derived_init(contract):
    for c in [contract] + contract.inheritance:
        init_functions = [f for f in c.functions_not_inherited if f.name == 'initialize']
        if len(init_functions) > 1:
            raise MultipleInitTarget
        if init_functions:
            return init_functions[0]
    return None

def check_initialization(s):

    initializable = s.get_contract_from_name('Initializable')

    if initializable is None:
        logger.info(yellow('Initializable contract not found, the contract does not follow a standard initalization schema.'))
        return

    initializer = initializable.get_modifier_from_signature('initializer()')

    init_info = ''

    double_calls_found = False
    missing_call = False
    initializer_modifier_missing = False

    for contract in s.contracts:
        if initializable in contract.inheritance:
            all_init_functions = _get_initialize_functions(contract)
            for f in all_init_functions:
                if not initializer in f.modifiers:
                    initializer_modifier_missing = True
                    logger.info(red(f'{f.contract.name}.{f.name} does not call initializer'))
            most_derived_init = _get_most_derived_init(contract)
            if most_derived_init is None:
                init_info += f'{contract.name} has no initialize function\n'
                continue
            else:
                init_info += f'{contract.name} needs to be initialized by {most_derived_init.full_name}\n'
            all_init_functions_called = _get_all_internal_calls(most_derived_init)  + [most_derived_init]
            missing_calls = [f for f in all_init_functions if not f in all_init_functions_called]
            for f in missing_calls:
                logger.info(red(f'Missing call to {f.contract.name}.{f.name} in {contract.name}'))
                missing_call = True
            double_calls = [f for f in all_init_functions_called if all_init_functions_called.count(f) > 1]
            for f in double_calls:
                logger.info(red(f'{f.contract.name + "." + f.full_name} is called multiple time in {contract.name}'))
                double_calls_found = True

    if not initializer_modifier_missing:
        logger.info(green('All the init functions have the initiliazer modifier'))

    if not double_calls_found:
        logger.info(green('No double call to init functions found'))

    if not missing_call:
        logger.info(green('No missing call to an init function found'))

    logger.info(green('Check the deployement script to ensure that these functions are called:\n'+ init_info))
