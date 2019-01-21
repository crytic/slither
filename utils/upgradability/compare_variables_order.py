'''
    This utility looks for functions collisions between a proxy and the implementation
    More for information: https://medium.com/nomic-labs-blog/malicious-backdoors-in-ethereum-proxies-62629adf3357
'''

import sys
from slither import Slither
from slither.utils.function import get_function_id
from slither.utils.colors import red, green

if __name__ == "__main__":

    if len(sys.argv) != 5:
        print('Usage: python3 compare_variables_order.py v1.sol Contract1 v2.sol Contract2')

    v1 = Slither(sys.argv[1])
    v2 = Slither(sys.argv[3])

    contract_v1 = v1.get_contract_from_name(sys.argv[2])
    if contract_v1 is None:
        print(red('Contract {} not found'.format(sys.argv[2])))
        exit(-1)

    contract_v2 = v2.get_contract_from_name(sys.argv[4])
    if contract_v2 is None:
        print(red('Contract {} not found'.format(sys.argv[4])))
        exit(-1)


    order_v1 = [(variable.name, variable.type) for variable in contract_v1.state_variables if not variable.is_constant]
    order_v2 = [(variable.name, variable.type) for variable in contract_v2.state_variables if not variable.is_constant]


    found = False
    for idx in range(0, len(order_v1)):
        (v1_name, v1_type) =  order_v1[idx]
        if len(order_v2) < idx:
            print(red('Missing variable in the new version: {} {}'.format(v1_name, v1_type)))
            continue
        (v2_name, v2_type) =  order_v2[idx]

        if (v1_name != v2_name) or (v1_type != v2_type):
            found = True
            print(red('Different variable: {} {} -> {} {}'.format(v1_name,
                                                                  v1_type,
                                                                  v2_name,
                                                                  v2_type)))

    if len(order_v2) > len(order_v1):
        new_variables = order_v2[len(order_v1):]
        for (name, t) in new_variables:
            print(green('New variable: {} {}'.format(name, t)))

    if not found:
        print(green('No error found'))

