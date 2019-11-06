'''
    Check for functions collisions between a proxy and the implementation
    More for information: https://medium.com/nomic-labs-blog/malicious-backdoors-in-ethereum-proxies-62629adf3357
'''

import logging
from slither import Slither
from slither.core.declarations import Function
from slither.exceptions import SlitherError
from slither.utils import json_utils
from slither.utils.function import get_function_id
from slither.utils.colors import red, green

logger = logging.getLogger("Slither-check-upgradeability")

def get_signatures(c):
    functions = c.functions
    functions = [f.full_name for f in functions if f.visibility in ['public', 'external'] and
                 not f.is_constructor and not f.is_fallback]

    variables = c.state_variables
    variables = [variable.name+ '()' for variable in variables if variable.visibility in ['public']]
    return list(set(functions+variables))


def _get_function_or_variable(contract, signature):
    f = contract.get_function_from_signature(signature)

    if f:
        return f

    for variable in contract.state_variables:
        # Todo: can lead to incorrect variable in case of shadowing
        if variable.visibility in ['public']:
            if variable.name + '()' == signature:
                return variable

    raise SlitherError(f'Function id checks: {signature} not found in {contract.name}')

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

                implem_function = _get_function_or_variable(implem, signatures_ids_implem[k])
                proxy_function = _get_function_or_variable(proxy, signatures_ids_proxy[k])

                info = f'Function id collision found: {implem_function.canonical_name} ({implem_function.source_mapping_str}) {proxy_function.canonical_name} ({proxy_function.source_mapping_str})'
                logger.info(red(info))
                json_elem = json_utils.generate_json_result(info)
                if isinstance(implem_function, Function):
                    json_utils.add_function_to_json(implem_function, json_elem)
                else:
                    json_utils.add_variable_to_json(implem_function, json_elem)
                if isinstance(proxy_function, Function):
                    json_utils.add_function_to_json(proxy_function, json_elem)
                else:
                    json_utils.add_variable_to_json(proxy_function, json_elem)
                results['function-id-collision'].append(json_elem)
                
            else:

                implem_function = _get_function_or_variable(implem, signatures_ids_implem[k])
                proxy_function = _get_function_or_variable(proxy, signatures_ids_proxy[k])

                info = f'Shadowing between {implem_function.canonical_name} ({implem_function.source_mapping_str}) and {proxy_function.canonical_name} ({proxy_function.source_mapping_str})'
                logger.info(red(info))

                json_elem = json_utils.generate_json_result(info)
                json_elem = json_utils.generate_json_result(info)
                if isinstance(implem_function, Function):
                    json_utils.add_function_to_json(implem_function, json_elem)
                else:
                    json_utils.add_variable_to_json(implem_function, json_elem)
                if isinstance(proxy_function, Function):
                    json_utils.add_function_to_json(proxy_function, json_elem)
                else:
                    json_utils.add_variable_to_json(proxy_function, json_elem)
                results['shadowing'].append(json_elem)

    if not error_found:
        logger.info(green('No error found'))

    return results
