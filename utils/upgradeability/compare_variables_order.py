'''
    Check if the variables respect the same ordering
'''
import logging
from slither import Slither
from slither.utils.function import get_function_id
from slither.utils.colors import red, green, yellow

logger = logging.getLogger("VariablesOrder")
logger.setLevel(logging.INFO)

def compare_variables_order_implementation(v1, contract_name1, v2, contract_name2):
    logger.info(green('Run variable order checks between the ' +
        'implementations... (see https://github.com/crytic/slither/wiki/' +
        'Upgradeability-Checks#variables-order-checks)'
    ))

    contract_v1 = __get_and_check_contracts_existence(v1, contract_name1)
    contract_v2 = __get_and_check_contracts_existence(v2, contract_name2)
    vars_v1 = __contract_state_variables(contract_v1)
    vars_v2 = __contract_state_variables(contract_v2)
    issues_found = False

    new_vars = [var for var in vars_v2 if not var in vars_v1]
    for (var_type, var_name) in new_vars:
        logger.info(green('New storage variable in {}: {} {}'.format(
            contract_name2,
            var_type,
            var_name
        )))

    missing_vars = [var for var in vars_v1 if not var in vars_v2]
    for (var_type, var_name) in missing_vars:
        issues_found = True
        logger.info(red('Missing storage variable in {}: {} {}'.format(
            contract_name2,
            var_type,
            var_name
        )))

    if __check_vars_order(contract_name1, contract_name2, vars_v1, vars_v2):
        issues_found = True

    if not issues_found:
        logger.info(green('No variable ordering issues found between implementations'))

def compare_variables_order_proxy(implem, implem_name, proxy, proxy_name):
    logger.info(green('Run variable order checks between the proxy and ' +
        'implementation... (see https://github.com/crytic/slither/wiki/' +
        'Upgradeability-Checks#variables-order-checks)'
    ))

    contract_implem = __get_and_check_contracts_existence(implem, implem_name)
    contract_proxy = __get_and_check_contracts_existence(proxy, proxy_name)
    vars_implem = __contract_state_variables(contract_implem)
    vars_proxy = __contract_state_variables(contract_proxy)
    issues_found = False

    for (var_type, var_name) in vars_proxy:
        logger.info(yellow('Storage variable defined in proxy {}: {} {}'.format(
            proxy_name,
            var_type,
            var_name
        )))

    extra_vars = [var for var in vars_proxy if not var in vars_implem]
    for (var_type, var_name) in extra_vars:
        issues_found = True
        logger.info(red('Extra storage variable in proxy {}: {} {}'.format(
            proxy_name,
            var_type,
            var_name
        )))

    if __check_vars_order(implem_name, proxy_name, vars_proxy, vars_implem):
        issues_found = True

    if not issues_found:
        logger.info(green('No variable ordering issues found between proxy and implementation'))

def __get_and_check_contracts_existence(source, name):
    contract = source.get_contract_from_name(name)
    if contract is None:
        logger.info(red('Contract {} not found in {}'.format(
            name,
            source.filename
        )))
        exit(-1)
    return contract

def __check_vars_order(old_name, new_name, vars_v1, vars_v2):
    issues_found = False
    for idx in range(len(vars_v1)):
        if idx >= len(vars_v2) or vars_v2[idx] != vars_v1[idx]:
            issues_found = True
            (v1_var_type, v1_var_name) = vars_v1[idx]

            msg = 'Order of storage variables in {} does not match {}. '
            msg += 'Expected declaration #{} in {} to be {} {}'
            msg = msg.format(
                new_name,
                old_name,
                idx+1,
                new_name,
                v1_var_type,
                v1_var_name
            )

            if idx < len(vars_v2):
                v2_var_type, v2_var_name = vars_v2[idx]
                msg += ', found {} {} instead.'.format(
                    v2_var_type,
                    v2_var_name
                )
            else:
                msg += '.'

            logger.info(red(msg))
    return issues_found

def __contract_state_variables(contract):
    return [(v.type, v.name) for v in contract.state_variables if not v.is_constant]
