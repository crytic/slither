"""
Tool to read on-chain storage from EVM
"""
import argparse

from crytic_compile import cryticparser

from slither import Slither
from slither.tools.read_storage.read_storage import get_storage_layout, get_storage_slot_and_val


def parse_args():
    """Parse the underlying arguments for the program.
    Returns:
        The arguments for the program.
    """
    parser = argparse.ArgumentParser(
        description="Read a variable's value from storage for a deployed contract",
        usage=(
            "\nTo retrieve a single variable's value:\n"
            + "\tslither-read-storage [codebase] address --variable-name NAME\n"
            + "To retrieve a contract's storage layout and values:\n"
            + "\tslither-read-storage [codebase] address --contract-name NAME --layout\n"
        ),
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
        help="The key/ index whose value will be returned from a deep mapping or multidimensional array",
        default=None,
    )

    parser.add_argument(
        "--struct-var",
        help="The name of the variable whose value will be returned from a struct",
        default=None,
    )

    parser.add_argument(
        "--storage-address",
        help="The address of the storage contract (if a proxy pattern is used)",
        default=None,
    )

    parser.add_argument(
        "--contract-name",
        help="The name of the logic contract",
        default=None,
    )

    parser.add_argument(
        "--layout",
        action="store_true",
        help="Toggle used to write a JSON file with the entire storage layout",
    )

    parser.add_argument("--max-depth", help="Max depth to search in data structure", default=20)

    cryticparser.init(parser)

    return parser.parse_args()


def main():
    args = parse_args()
    assert args.rpc_url
    if len(args.contract_source) == 2:
        # Source code is file .sol, project directory
        source_code, target = args.contract_source
        slither = Slither(source_code, **vars(args))
    else:
        # Source code is published and retrieved via etherscan
        target = args.contract_source[0]
        slither = Slither(target, **vars(args))

    if args.contract_name:
        contracts = slither.get_contract_from_name(args.contract_name)
    else:
        contracts = slither.contracts

    # Remove target prefix e.g. rinkeby:0x0 -> 0x0
    address = target[target.find(":") + 1 :]

    if args.layout:
        get_storage_layout(contracts, address, args.rpc_url, args.max_depth, args.storage_address)
    else:
        assert args.variable_name
        get_storage_slot_and_val(contracts, address, args.variable_name, args.rpc_url, **vars(args))


if __name__ == "__main__":
    main()
