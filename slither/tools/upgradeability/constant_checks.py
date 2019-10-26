import logging

from slither.utils.colors import red, yellow, green

logger = logging.getLogger("Slither-check-upgradeability")

def constant_conformance_check(contract_v1, contract_v2):

    results = {
        "became_constants": [],
        "were_constants": [],
        "not_found_in_v2": [],
    }

    logger.info(green(
        '\n## Run variable constants conformance check... (see https://github.com/crytic/slither/wiki/Upgradeability-Checks)'))
    error_found = False

    state_variables_v1 = contract_v1.state_variables
    state_variables_v2 = contract_v2.state_variables

    for idx in range(0, len(state_variables_v1)):
        state_v1 = contract_v1.state_variables[idx]

        if len(state_variables_v2) <= idx:
            break

        state_v2 = contract_v2.state_variables[idx]

        if state_v2:
            if state_v1.is_constant:
                if not state_v2.is_constant:
                    info = f'{state_v1.canonical_name} was constant and {contract_v2.name} is not'
                    logger.info(red(info))
                    results['were_constants'].append({
                        'description': info,
                        'contract_v1': contract_v1.name,
                        'contract_v2': contract_v2.name,
                        'variable': state_v1.name,
                        'source_mapping': state_v1.source_mapping
                    })
                    error_found = True
            elif state_v2.is_constant:
                info = f'{state_v1.canonical_name} was not constant and {contract_v2.name} is'
                logger.info(red(info))
                results['became_constants'].append({
                    'description': info,
                    'contract_v1': contract_v1.name,
                    'contract_v2': contract_v2.name,
                    'variable': state_v1.name,
                    'source_mapping': state_v1.source_mapping
                })
                error_found = True

        else:
            info = f'{state_v1.canonical_name} not found in {contract_v2.name}, not check was done'
            logger.info(yellow(info))
            results['not_found_in_v2'].append({
                'description': info,
                'contract_v1': contract_v1.name,
                'contract_v2': contract_v2.name,
                'variable': state_v1.name,
                'source_mapping': state_v1.source_mapping
            })
            error_found = True

    if not error_found:
        logger.info(green('No error found'))

    return results