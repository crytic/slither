'''
    Check if the variables respect the same ordering
'''
import logging
from slither import Slither
from slither.utils.function import get_function_id
from slither.utils.colors import red, green, yellow
from slither.exceptions import SlitherException

logger = logging.getLogger("VariablesOrder")
logger.setLevel(logging.INFO)

def compare_variables_order_implementation(v1, contract_name1, v2, contract_name2):

    results = {}
    
    logger.info(green('Run variables order checks between implementations... (see https://github.com/crytic/slither/wiki/Upgradeability-Checks#variables-order-checks)'))

    contract_v1 = v1.get_contract_from_name(contract_name1)
    if contract_v1 is None:
        info = 'Contract {} not found in {}'.format(contract_name1, v1.filename)
        logger.info(red(info))
        raise SlitherException(info)

    contract_v2 = v2.get_contract_from_name(contract_name2)
    if contract_v2 is None:
        info = 'Contract {} not found in {}'.format(contract_name2, v2.filename)
        logger.info(red(info))
        raise SlitherException(info)

    order_v1 = [(variable.name, variable.type) for variable in contract_v1.state_variables if not variable.is_constant]
    order_v2 = [(variable.name, variable.type) for variable in contract_v2.state_variables if not variable.is_constant]

    results['missing-variable'] = []
    results['different-variables'] = []
    found = False
    for idx in range(0, len(order_v1)):
        (v1_name, v1_type) =  order_v1[idx]
        if len(order_v2) < idx:
            info = 'Missing variable in the new version: {} {}'.format(v1_name, v1_type)
            logger.info(red(info))
            results['missing-variable'].append(info)
            continue
        (v2_name, v2_type) =  order_v2[idx]

        if (v1_name != v2_name) or (v1_type != v2_type):
            found = True
            info = 'Different variables between v1 and v2: {} {} -> {} {}'.format(v1_name, v1_type, v2_name, v2_type)
            logger.info(red(info))
            results['different-variables'].append(info)

    if len(order_v2) > len(order_v1):
        new_variables = order_v2[len(order_v1):]
        for (name, t) in new_variables:
            logger.info(green('New variable: {} {}'.format(name, t)))

    if not found:
        logger.info(green('No variables ordering error found between implementations'))

    return results


def compare_variables_order_proxy(implem, implem_name, proxy, proxy_name):

    results = {}
    
    logger.info(green('Run variables order checks between the implementation and the proxy... (see https://github.com/crytic/slither/wiki/Upgradeability-Checks#variables-order-checks)'))

    contract_implem = implem.get_contract_from_name(implem_name)
    if contract_implem is None:
        info = 'Contract {} not found in {}'.format(implem_name, implem.filename)
        logger.info(red(info))
        raise SlitherException(info)

    contract_proxy = proxy.get_contract_from_name(proxy_name)
    if contract_proxy is None:
        info = 'Contract {} not found in {}'.format(proxy_name, proxy.filename)
        logger.info(red(info))
        raise SlitherException(info)

    order_implem = [(variable.name, variable.type) for variable in contract_implem.state_variables if not variable.is_constant]
    order_proxy = [(variable.name, variable.type) for variable in contract_proxy.state_variables if not variable.is_constant]


    results['extra-variable'] = []
    results['different-variables'] = []
    found = False
    for idx in range(0, len(order_proxy)):
        (proxy_name, proxy_type) =  order_proxy[idx]
        if len(order_implem) <= idx:
            info = 'Extra variable in the proxy: {} {}'.format(proxy_name, proxy_type)
            logger.info(red(info))
            results['extra-variable'].append(info)
            continue
        (implem_name, implem_type) =  order_implem[idx]

        if (proxy_name != implem_name) or (proxy_type != implem_type):
            found = True
            info = 'Different variables between proxy and implem: {} {} -> {} {}'.format(proxy_name,
                                                                                         proxy_type,
                                                                                         implem_name,
                                                                                         implem_type)
            logger.info(red(info))
            results['different-variables'].append(info)
        else:
            logger.info(yellow('Variable in the proxy: {} {}'.format(proxy_name,
                                                                     proxy_type)))


    #if len(order_implem) > len(order_proxy):
    #    new_variables = order_implem[len(order_proxy):]
    #    for (name, t) in new_variables:
    #        logger.info(green('Variable only in implem: {} {}'.format(name, t)))

    if not found:
        logger.info(green('No variables ordering error found between implementation and the proxy'))


    return results
