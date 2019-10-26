import logging

from slither.utils import json_utils
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
            json_elem = json_utils.generate_json_result(info)
            json_utils.add_variable_to_json(s, json_elem)
            results['variables-initialized'].append(json_elem)
            error_found = True

    if not error_found:
        logger.info(green('No error found'))

    return results