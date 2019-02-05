import logging
import argparse
import sys

from slither import Slither

from .compare_variables_order import compare_variables_order_implementation, compare_variables_order_proxy
from .compare_function_ids import compare_function_ids

logging.basicConfig()
logger = logging.getLogger("Slither-check-upgradability")

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

    proxy = Slither(vars(args)['proxy.sol'], solc=args.solc)
    proxy_name = args.ProxyName
    v1 = Slither(vars(args)['implem.sol'], solc=args.solc)
    v1_name = args.ContractName

    last_contract = v1
    last_name = v1_name

    if args.new_version:
        v2 = Slither(args.new_version, solc=args.solc)
        last_contract = v2

    if args.new_contract_name:
        last_name = args.new_contract_name

    compare_function_ids(last_contract, proxy)
    compare_variables_order_proxy(last_contract, last_name, proxy, proxy_name)

    if args.new_version:
        compare_variables_order_implementation(v1, v1_name, v2, last_name)
