import logging

from slither.utils import json_utils
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

    v2_additional_variables = len(state_variables_v2) - len(state_variables_v1)
    if v2_additional_variables < 0:
        v2_additional_variables = 0

    # We keep two index, because we need to have them out of sync if v2
    # has additional non constant variables
    idx_v1 = 0
    idx_v2 = 0
    while idx_v1 < len(state_variables_v1):

        state_v1 = contract_v1.state_variables[idx_v1]
        if len(state_variables_v2) <= idx_v2:
            break

        state_v2 = contract_v2.state_variables[idx_v2]

        if state_v2:
            if state_v1.is_constant:
                if not state_v2.is_constant:

                    # If v2 has additional non constant variables, we need to skip them
                    if (state_v1.name != state_v2.name or state_v1.type != state_v2.type) and v2_additional_variables>0:
                        v2_additional_variables -= 1
                        idx_v2 += 1
                        continue

                    info = f'{state_v1.canonical_name} ({state_v1.source_mapping_str}) was constant and {state_v2.canonical_name} is not ({state_v2.source_mapping_str})'
                    logger.info(red(info))

                    json_elem = json_utils.generate_json_result(info)
                    json_utils.add_variable_to_json(state_v1, json_elem)
                    json_utils.add_variable_to_json(state_v2, json_elem)
                    results['were_constants'].append(json_elem)
                    error_found = True

            elif state_v2.is_constant:
                info = f'{state_v1.canonical_name} ({state_v1.source_mapping_str}) was not constant but {state_v2.canonical_name} is ({state_v2.source_mapping_str})'
                logger.info(red(info))

                json_elem = json_utils.generate_json_result(info)
                json_utils.add_variable_to_json(state_v1, json_elem)
                json_utils.add_variable_to_json(state_v2, json_elem)
                results['became_constants'].append(json_elem)
                error_found = True

        else:
            info = f'{state_v1.canonical_name} not found in {contract_v2.name}, not check was done'
            logger.info(yellow(info))

            json_elem = json_utils.generate_json_result(info)
            json_utils.add_variable_to_json(state_v1, json_elem)
            json_utils.add_contract_to_json(contract_v2, json_elem)
            results['not_found_in_v2'].append(json_elem)

            error_found = True

        idx_v1 += 1
        idx_v2 += 1

    if not error_found:
        logger.info(green('No error found'))

    return results