import argparse
import logging
import os
import re

from slither.slither import Slither

from slither.exceptions import SlitherError

logging.basicConfig()
logger = logging.getLogger("Slither-upload-etherscan")


def parse_args():
    """
    Parse the underlying arguments for the program.
    :return: Returns the arguments for the program.
    """
    parser = argparse.ArgumentParser(description='Contracts flattening',
                                     usage='slither-upload-etherscan --contract contractname \
                                            --address contractaddress')
    parser.add_argument('--address',
                        help='Contract address to be verified')

    parser.add_argument('--contract',
                        help='Flatten a specific contract (default: all most derived contracts).',
                        default=None)

    # Add default arguments from crytic-compile
    # cryticparser.init(parser)

    return parser.parse_args()


def check_contract_address(contract_address):
    if contract_address.endswith(".sol"):
        raise SlitherError("Please input contract address!")

    if contract_address.startswith("0x"):
        if len(contract_address) != 42:
            raise SlitherError("Please check your contract address, it is invalid")
    else:
        if len(contract_address) != 40:
            raise SlitherError("Please check your contract address, it is invalid")
        else:
            contract_address = "0x" + contract_address

    pattern = re.compile(r'^[A-Fa-f0-9]{40}$')
    if not pattern.match(contract_address[2:]):
        raise SlitherError("You contract address contains invalid character")

    return contract_address


def check_input(contract_file, contract_address):
    if not os.path.exists(contract_file):
        raise SlitherError("Contract file does not exist!")
    check_contract_address(contract_address)


def main():
    args = parse_args()

    contract_file = args.contract
    contract_address = args.address

    check_input(contract_file, contract_address)

    # Init slither
    slither = Slither(contract_file)
    source_code = slither.source_code

    start_path = os.getcwd()
    flatten_file_path = os.path.join(start_path, 'flattenContracts.sol')
    with open(flatten_file_path, 'a', encoding='utf8') as f:
        for _, contract_code in source_code.items():
            contract_code = contract_code.replace('import', '// import')
            f.write(contract_code)
