"""
Tool to read on-chain storage from EVM
"""
import json
import argparse

from crytic_compile import cryticparser

from slither import Slither
from slither.tools.read_storage.read_storage import SlitherReadStorage


def parse_args() -> argparse.Namespace:
    """Parse the underlying arguments for the program.
    Returns:
        The arguments for the program.
    """
    parser = argparse.ArgumentParser(
        description="Read a variable's value from storage for a deployed contract",
        usage=(
            "\nTo retrieve a single variable's value:\n"
            + "\tslither-read-storage $TARGET address --variable-name $NAME\n"
            + "To retrieve a contract's storage layout:\n"
            + "\tslither-read-storage $TARGET address --contract-name $NAME --json storage_layout.json\n"
            + "To retrieve a contract's storage layout and values:\n"
            + "\tslither-read-storage $TARGET address --contract-name $NAME --json storage_layout.json --value\n"
            + "TARGET can be a contract address or project directory"
        ),
    )

    parser.add_argument(
        "contract_source",
        help="The deployed contract address if verified on etherscan. Prepend project directory for unverified contracts.",
        nargs="+",
    )

    parser.add_argument(
        "--variable-name",
        help="The name of the variable whose value will be returned.",
        default=None,
    )

    parser.add_argument("--rpc-url", help="An endpoint for web3 requests.")

    parser.add_argument(
        "--key",
        help="The key/ index whose value will be returned from a mapping or array.",
        default=None,
    )

    parser.add_argument(
        "--deep-key",
        help="The key/ index whose value will be returned from a deep mapping or multidimensional array.",
        default=None,
    )

    parser.add_argument(
        "--struct-var",
        help="The name of the variable whose value will be returned from a struct.",
        default=None,
    )

    parser.add_argument(
        "--storage-address",
        help="The address of the storage contract (if a proxy pattern is used).",
        default=None,
    )

    parser.add_argument(
        "--contract-name",
        help="The name of the logic contract.",
        default=None,
    )

    parser.add_argument(
        "--json",
        action="store",
        help="Save the result in a JSON file.",
    )

    parser.add_argument(
        "--value",
        action="store_true",
        help="Toggle used to include values in output.",
    )

    parser.add_argument(
        "--table",
        action="store_true",
        help="Print table view of storage layout",
    )

    parser.add_argument(
        "--silent",
        action="store_true",
        help="Silence log outputs",
    )

    parser.add_argument("--max-depth", help="Max depth to search in data structure.", default=20)

    parser.add_argument(
        "--block",
        help="The block number to read storage from. Requires an archive node to be provided as the RPC url.",
        default="latest",
    )

    cryticparser.init(parser)

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if len(args.contract_source) == 2:
        # Source code is file.sol or project directory
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

    srs = SlitherReadStorage(contracts, args.max_depth)

    if args.block:
        try:
            srs.block = int(args.block)
        except ValueError:
            srs.block = str(args.block)

    if args.rpc_url:
        # Remove target prefix e.g. rinkeby:0x0 -> 0x0.
        address = target[target.find(":") + 1 :]
        # Default to implementation address unless a storage address is given.
        if not args.storage_address:
            args.storage_address = address
        srs.storage_address = args.storage_address

        srs.rpc = args.rpc_url

    if args.variable_name:
        # Use a lambda func to only return variables that have same name as target.
        # x is a tuple (`Contract`, `StateVariable`).
        srs.get_all_storage_variables(lambda x: bool(x[1].name == args.variable_name))
        srs.get_target_variables(**vars(args))
    else:
        srs.get_all_storage_variables()
        srs.get_storage_layout()

    # To retrieve slot values an rpc url is required.
    if args.value:
        assert args.rpc_url
        srs.walk_slot_info(srs.get_slot_values)

    if args.table:
        srs.walk_slot_info(srs.convert_slot_info_to_rows)
        print(srs.table)

    if args.json:
        with open(args.json, "w", encoding="utf-8") as file:
            slot_infos_json = srs.to_json()
            json.dump(slot_infos_json, file, indent=4)


if __name__ == "__main__":
    main()
