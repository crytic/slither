'''
    Check for functions collisions between a proxy and the implementation
    More for information: https://medium.com/nomic-labs-blog/malicious-backdoors-in-ethereum-proxies-62629adf3357
'''

import logging
from slither import Slither
from slither.utils.function import get_function_id
from slither.utils.colors import red, green

logger = logging.getLogger("CompareFunctions")
logger.setLevel(logging.INFO)

def get_signatures(c):
    functions = c.functions
    functions = [f.full_name for f in functions if f.visibility in ['public', 'external'] and not f.is_constructor]

    variables = c.state_variables
    variables = [variable.name+ '()' for variable in variables if variable.visibility in ['public']]
    return list(set(functions+variables))


def compare_function_ids(implem, implem_name, proxy, proxy_name):

    results = {}
    
    logger.info(green('Run function ids checks... (see https://github.com/crytic/slither/wiki/Upgradeability-Checks#functions-ids-checks)'))

    implem_contract = implem.get_contract_from_name(implem_name)
    if implem_contract is None:
        info = f'{implem_name} not found in {implem.filename}'
        logger.info(red(info))
        results['implementation-contract-not-found'] = info
        return results
    proxy_contract = proxy.get_contract_from_name(proxy_name)
    if proxy_contract is None:
        info = f'{proxy_name} not found in {proxy.filename}'
        logger.info(red(info))
        results['proxy-contract-not-found'] = info
        return results

    signatures_implem = get_signatures(implem_contract)
    signatures_proxy = get_signatures(proxy_contract)

    signatures_ids_implem = {get_function_id(s): s for s in signatures_implem}
    signatures_ids_proxy = {get_function_id(s): s for s in signatures_proxy}

    found = False
    for (k, _) in signatures_ids_implem.items():
        if k in signatures_ids_proxy:
            found = True
            if signatures_ids_implem[k] != signatures_ids_proxy[k]:
                info = 'Function id collision found {} {}'.format(signatures_ids_implem[k], signatures_ids_proxy[k])
                logger.info(red(info))
                results['function-id-collision'] = info
                
            else:
                info = 'Shadowing between proxy and implementation found {}'.format(signatures_ids_implem[k])
                logger.info(red(info))
                results['shadowing'] = info

    if not found:
        logger.info(green('No function ids collision found'))

    return results
