'''
    Check for functions collisions between a proxy and the implementation
    More for information: https://medium.com/nomic-labs-blog/malicious-backdoors-in-ethereum-proxies-62629adf3357
'''

import logging
from slither import Slither
from slither.utils.function import get_function_id
from slither.utils.colors import red, green

logger = logging.getLogger("Slither-check-upgradeability")

def get_signatures(c):
    functions = c.functions
    functions = [f.full_name for f in functions if f.visibility in ['public', 'external'] and not f.is_constructor]

    variables = c.state_variables
    variables = [variable.name+ '()' for variable in variables if variable.visibility in ['public']]
    return list(set(functions+variables))


def compare_function_ids(implem, proxy):

    results = {
        'function-id-collision':[],
        'shadowing':[],
    }
    
    logger.info(green('\n## Run function ids checks... (see https://github.com/crytic/slither/wiki/Upgradeability-Checks#functions-ids-checks)'))

    signatures_implem = get_signatures(implem)
    signatures_proxy = get_signatures(proxy)

    signatures_ids_implem = {get_function_id(s): s for s in signatures_implem}
    signatures_ids_proxy = {get_function_id(s): s for s in signatures_proxy}

    error_found = False
    for (k, _) in signatures_ids_implem.items():
        if k in signatures_ids_proxy:
            error_found = True
            if signatures_ids_implem[k] != signatures_ids_proxy[k]:
                info = 'Function id collision found {} {}'.format(signatures_ids_implem[k], signatures_ids_proxy[k])
                logger.info(red(info))
                results['function-id-collision'].append({
                    'description': info,
                    'function1': signatures_ids_implem[k],
                    'function2': signatures_ids_proxy[k],
                })
                
            else:
                info = 'Shadowing between proxy and implementation found {}'.format(signatures_ids_implem[k])
                logger.info(red(info))
                results['shadowing'].append({
                    'function': signatures_ids_implem[k]
                })

    if not error_found:
        logger.info(green('No error found'))

    return results
