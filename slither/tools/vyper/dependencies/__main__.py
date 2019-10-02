import logging
import argparse
import sys

from slither import Slither
from crytic_compile import cryticparser
from slither.utils.colors import red, green

logging.basicConfig()
logger = logging.getLogger("Slither-dependencies")
logger.setLevel(logging.INFO)
logging.getLogger("Slither").setLevel(logging.INFO)


def parse_args():

    parser = argparse.ArgumentParser(description='Vyper dependencies Checks. For usage information see [].',
                                     usage="slither-dependencies contract1.vy contract2.vy contract3.vy")

    parser.add_argument('contracts', nargs='*')

    cryticparser.init(parser)

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    return parser.parse_args()

def main():
    args = parse_args()

    all_functions = {}
    slithers = []
    for contract in args.contracts:
        s = Slither(contract, **vars(args))
        slithers.append(s)
        contract_instance = s.get_contract_from_name(contract[:-len('.vy')])
        all_functions[contract_instance.name] = [f.signature_str for f in contract_instance.functions]

    error_found = False
    for s in slithers:
        for contract in s.contracts:
            if contract.name in all_functions:
                for f in contract.functions:
                    if not f.signature_str in all_functions[contract.name]:
                        logger.info(red(f'{f.signature_str} does not exist in {contract.name}'))
                        error_found = True

    if not error_found:
        logger.info(green('No error found'))





