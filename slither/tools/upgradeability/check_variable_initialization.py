import logging

from slither.utils.colors import red, green

logger = logging.getLogger("Slither-check-upgradeability")


def check_variable_initialization(contract):
    results = {
        'variables-initialized': []
    }

    logger.info(green(
        '\n## Run variable initialization checks... (see https://github.com/crytic/slither/wiki/Upgradeability-Checks)'))

    error_found = False

    for s in contract.state_variables:
        if s.initialized and not s.is_constant:
            info = f'{s.canonical_name} has an initial value ({s.source_mapping_str})'
            logger.info(red(info))
            results['variables-initialized'].append(
                {
                    'description': info,
                    'name': s.name,
                    'contract': s.contract.name,
                    'source_mapping': s.source_mapping
                }
            )
            error_found = True

    if not error_found:
        logger.info(green('No error found'))

    return results