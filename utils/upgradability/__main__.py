import logging
import argparse
import sys

from slither import Slither

from .compare_variables_order import compare_variables_order
from .compare_function_ids import compare_function_ids

logging.basicConfig()
logger = logging.getLogger("Slither-check-upgradability")

def parse_args():

    parser = argparse.ArgumentParser(description='Slither Upgradability Checks',
                                     usage="slither-check-upgradability proxy.sol ProxyName v1.sol V1Name v2.sol V2Name")


    parser.add_argument('proxy.sol', help='Proxy filename')
    parser.add_argument('ProxyName', help='Contract name')

    parser.add_argument('v1.sol', help='Version 1 filename')
    parser.add_argument('V1Name', help='Contract name')

    parser.add_argument('v2.sol', help='Version 2 filename')
    parser.add_argument('V2Name', help='Contract name')

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    return parser.parse_args()

def main():
    args = parse_args()


    proxy = Slither(vars(args)['proxy.sol'])
    proxy_name = args.ProxyName
    v1 = Slither(vars(args)['v1.sol'])
    v1_name = args.V1Name
    v2 = Slither(vars(args)['v2.sol'])
    v2_name = args.V2Name

    compare_variables_order(v1, v1_name, v2, v2_name)
    compare_function_ids(v2, proxy)
