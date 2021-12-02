"""
Tool to read on-chain storage from EVM
"""
import argparse

from crytic_compile import cryticparser

from slither import Slither
from slither.tools.read_storage.read_storage import get_storage_layout, get_storage_slot_and_val


def parse_args():
    """
    Parse the underlying arguments for the program.
    :return: Returns the arguments for the program.
    """
    parser = argparse.ArgumentParser(
        description="Read a variable's value from storage for a deployed contract",
        usage="slither-read-storage [codebase] address variable_name",
    )

    parser.add_argument(
        "contract_source",
        help="The deployed contract address on mainnet and project directory for unverified contracts",
        nargs="+",
    )

    parser.add_argument(
        "--variable-name",
        help="The name of the variable whose value will be returned",
        default=None,
    )

    parser.add_argument("--rpc-url", help="An endpoint for web3 requests")

    parser.add_argument(
        "--key",
        help="The key/ index whose value will be returned from a mapping or array",
        default=None,
    )

    parser.add_argument(
        "--deep-key",
        help="The key whose value will be returned from a mapping within a mapping",
        default=None,
    )

    parser.add_argument(
        "--struct-var",
        help="The name of the variable whose value will be returned from a struct",
        default=None,
    )

    parser.add_argument(
        "--storage-address",
        help="The name of the variable whose value will be returned from a struct",
        default=None,
    )

    parser.add_argument(
        "--contract-name",
        help="The name of the variable whose value will be returned from a struct",
        default=None,
    )

    parser.add_argument("--layout", help="An endpoint for web3 requests")

    cryticparser.init(parser)

    return parser.parse_args()


def main():
    args = parse_args()
    assert args.rpc_url
    if len(args.contract_source) == 2:
        source_code, target = args.contract_source  # Source code is file .sol, project directory
        slither = Slither(source_code, **vars(args))
    else:
        target = args.contract_source[0]  # Source code is published and retrieved via etherscan
        slither = Slither(target, **vars(args))

    if args.contract_name:
        contracts = slither.get_contract_from_name(args.contract_name)
    else:
        contracts = slither.contracts

    address = target[target.find(":") + 1 :]  # Remove target prefix e.g. rinkeby:0x0 -> 0x0
    if args.layout:
        get_storage_layout(contracts, address, **vars(args))
    else:
        get_storage_slot_and_val(contracts, address, **vars(args))


if __name__ == "__main__":
    main()
