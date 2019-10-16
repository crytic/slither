import logging
import argparse
import sys
import json

from slither import Slither
from crytic_compile import cryticparser

from .compare_variables_order import compare_variables_order_implementation, compare_variables_order_proxy
from .compare_function_ids import compare_function_ids
from .check_initialization import check_initialization

from collections import OrderedDict

logging.basicConfig()
logging.getLogger("Slither-check-upgradeability").setLevel(logging.INFO)
logging.getLogger("Slither").setLevel(logging.INFO)

def parse_args():

    parser = argparse.ArgumentParser(description='Slither Upgradeability Checks. For usage information see https://github.com/crytic/slither/wiki/Upgradeability-Checks.',
                                     usage="slither-check-upgradeability proxy.sol ProxyName implem.sol ContractName")


    parser.add_argument('proxy.sol', help='Proxy filename')
    parser.add_argument('ProxyName', help='Contract name')

    parser.add_argument('implem.sol', help='Implementation filename')
    parser.add_argument('ContractName', help='Contract name')

    parser.add_argument('--new-version', help='New implementation filename')
    parser.add_argument('--new-contract-name', help='New contract name (if changed)')

    cryticparser.init(parser)

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    return parser.parse_args()

def main():
    args = parse_args()

    proxy_filename = vars(args)['proxy.sol']
    proxy = Slither(proxy_filename, **vars(args))
    proxy_name = args.ProxyName

    v1_filename = vars(args)['implem.sol']
    v1 = Slither(v1_filename, **vars(args))
    v1_name = args.ContractName

    results = OrderedDict()
    
    results['check_initialization'] = check_initialization(v1)

    if not args.new_version:
        results['compare_function_ids'] = compare_function_ids(v1, v1_name, proxy, proxy_name)
        results['compare_variables_order_proxy'] = compare_variables_order_proxy(v1, v1_name, proxy, proxy_name)
    else:
        v2 = Slither(args.new_version, **vars(args))
        v2_name = v1_name if not args.new_contract_name else args.new_contract_name
        results['check_initialization_v2'] = check_initialization(v2)
        results['compare_function_ids'] = compare_function_ids(v2, v2_name, proxy, proxy_name)
        results['compare_variables_order_proxy'] = compare_variables_order_proxy(v2, v2_name, proxy, proxy_name)
        results['compare_variables_order_implementation'] = compare_variables_order_implementation(v1, v1_name, v2, v2_name)

    with open('results.json', 'w') as fp:
        json.dump(results, fp)
