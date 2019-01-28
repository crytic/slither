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

def get_signatures(s):
    functions = [contract.functions for contract in s.contracts_derived]
    functions = [item for sublist in functions for item in sublist]
    functions = [f.full_name for f in functions if f.visibility in ['public', 'external']]

    variables = [contract.state_variables for contract in s.contracts_derived]
    variables = [item for sublist in variables for item in sublist]
    variables = [variable.name+ '()' for variable in variables if variable.visibility in ['public']]
    return list(set(functions+variables))


def compare_function_ids(implem, proxy):

    signatures_implem = get_signatures(implem)
    signatures_proxy = get_signatures(proxy)

    signatures_ids_implem = {get_function_id(s): s for s in signatures_implem}
    signatures_ids_proxy = {get_function_id(s): s for s in signatures_proxy}

    found = False
    for (k, _) in signatures_ids_implem.items():
        if k in signatures_ids_proxy:
            found = True
            logger.info(red('Collision found {} {}'.format(signatures_ids_implem[k],
                                                           signatures_ids_proxy[k])))

    if not found:
        logger.info(green('No collision found'))

