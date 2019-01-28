'''
    Check if the variables respect the same ordering
'''
import logging
from slither import Slither
from slither.utils.function import get_function_id
from slither.utils.colors import red, green

logger = logging.getLogger("VariablesOrder")
logger.setLevel(logging.INFO)

def compare_variables_order(v1, contract_name1, v2, contract_name2):

    contract_v1 = v1.get_contract_from_name(contract_name1)
    if contract_v1 is None:
        logger.info(red('Contract {} not found'.format(contract_name1)))
        exit(-1)

    contract_v2 = v2.get_contract_from_name(contract_name2)
    if contract_v2 is None:
        logger.info(red('Contract {} not found'.format(contract_name2)))
        exit(-1)


    order_v1 = [(variable.name, variable.type) for variable in contract_v1.state_variables if not variable.is_constant]
    order_v2 = [(variable.name, variable.type) for variable in contract_v2.state_variables if not variable.is_constant]


    found = False
    for idx in range(0, len(order_v1)):
        (v1_name, v1_type) =  order_v1[idx]
        if len(order_v2) < idx:
            logger.info(red('Missing variable in the new version: {} {}'.format(v1_name, v1_type)))
            continue
        (v2_name, v2_type) =  order_v2[idx]

        if (v1_name != v2_name) or (v1_type != v2_type):
            found = True
            logger.info(red('Different variable: {} {} -> {} {}'.format(v1_name,
                                                                        v1_type,
                                                                        v2_name,
                                                                  v2_type)))

    if len(order_v2) > len(order_v1):
        new_variables = order_v2[len(order_v1):]
        for (name, t) in new_variables:
            logger.info(green('New variable: {} {}'.format(name, t)))

    if not found:
        logger.info(green('No error found'))

