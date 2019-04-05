import os
import logging
import argparse
import sys

from slither import Slither

from .compare_variables_order import compare_variables_order_implementation, compare_variables_order_proxy
from .compare_function_ids import compare_function_ids
from .check_initialization import check_initialization

logging.basicConfig()
logging.getLogger("Slither-check-upgradability").setLevel(logging.INFO)
logging.getLogger("Slither").setLevel(logging.INFO)


def parse_args():

    parser = argparse.ArgumentParser(description='Slither Upgradability Checks',
                                     usage="slither-check-upgradability proxy.sol ProxyName implem.sol ContractName")


    parser.add_argument('proxy.sol', help='Proxy filename')
    parser.add_argument('ProxyName', help='Contract name')

    parser.add_argument('implem.sol', help='Implementation filename')
    parser.add_argument('ContractName', help='Contract name')

    parser.add_argument('--new-version', help='New implementation filename')
    parser.add_argument('--new-contract-name', help='New contract name (if changed)')
    parser.add_argument('--solc', help='solc path', default='solc')

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    return parser.parse_args()

def main():
    args = parse_args()

    proxy_filename = vars(args)['proxy.sol']
    proxy = Slither(proxy_filename, solc=args.solc, disable_solc_warnings=True)
    proxy_name = args.ProxyName

    v1_filename = vars(args)['implem.sol']
    v1 = Slither(v1_filename, solc=args.solc, disable_solc_warnings=True)
    v1_name = args.ContractName

    check_initialization(v1)

    if not args.new_version:
        compare_function_ids(v1, v1_name, proxy, proxy_name)
        compare_variables_order_proxy(v1, v1_name, proxy, proxy_name)
    else:
        v2 = Slither(args.new_version, solc=args.solc, disable_solc_warnings=True)
        v2_name = v1_name if not args.new_contract_name else args.new_contract_name
        check_initialization(v2)
        compare_function_ids(v2, v2_name, proxy, proxy_name)
        compare_variables_order_proxy(v2, v2_name, proxy, proxy_name)
        compare_variables_order_implementation(v1, v1_name, v2, v2_name)
