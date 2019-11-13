'''
    Check if the variables respect the same ordering
'''
import logging

from slither.utils.output import Output
from slither.utils.colors import red, green, yellow

logger = logging.getLogger("Slither-check-upgradeability")


def compare_variables_order(contract1, contract2, missing_variable_check=True):

    results = {
        'missing_variables': [],
        'different-variables': [],
        'extra-variables': []
    }

    logger.info(green(
        f'\n## Run variables ordering checks between {contract1.name} and {contract2.name}... (see https://github.com/crytic/slither/wiki/Upgradeability-Checks#variables-order-checks)'))

    order1 = [variable for variable in contract1.state_variables if not variable.is_constant]
    order2 = [variable for variable in contract2.state_variables if not variable.is_constant]

    error_found = False
    idx = 0
    for idx in range(0, len(order1)):
        variable1 = order1[idx]
        if len(order2) <= idx:
            if missing_variable_check:
                info = f'Variable only in {contract1.name}: {variable1.name} ({variable1.source_mapping_str})'
                logger.info(yellow(info))

                res = Output(info)
                res.add(variable1)
                results['missing_variables'].append(res.data)

                error_found = True
            continue

        variable2 = order2[idx]

        if (variable1.name != variable2.name) or (variable1.type != variable2.type):
            info = f'Different variables between {contract1.name} and {contract2.name}:\n'
            info += f'\t Variable {idx} in {contract1.name}: {variable1.name} {variable1.type} ({variable1.source_mapping_str})\n'
            info += f'\t Variable {idx} in {contract2.name}: {variable2.name} {variable2.type} ({variable2.source_mapping_str})\n'
            logger.info(red(info))

            res = Output(info, additional_fields={'index': idx})
            res.add(variable1)
            res.add(variable2)
            results['different-variables'].append(res.data)

            error_found = True

    idx = idx + 1

    while idx < len(order2):
        variable2 = order2[idx]

        info = f'Extra variables in {contract2.name}: {variable2.name} ({variable2.source_mapping_str})\n'
        logger.info(yellow(info))
        res = Output(info, additional_fields={'index': idx})
        res.add(variable2)
        results['extra-variables'].append(res.data)
        idx = idx + 1

    if not error_found:
        logger.info(green('No error found'))

    return results

