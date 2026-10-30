"""
Tool to read on-chain storage from EVM
"""

import json
import argparse
import os

from crytic_compile import cryticparser

from slither import Slither
from slither.exceptions import SlitherError
from slither.tools.read_storage.read_storage import SlitherReadStorage, RpcInfo

# Top-level keys expected in a solc Standard JSON *input* file, see
# https://docs.soliditylang.org/en/latest/using-the-compiler.html#input-description
_STANDARD_JSON_REQUIRED_KEYS = ("language", "sources")


def _is_solc_standard_json(path: str) -> bool:
    """Best-effort check for whether `path` is a solc Standard JSON input file.

    This lets users point slither-read-storage directly at a Standard JSON file
    (e.g. produced by `solc --standard-json` tooling, or hand-built) instead of
    requiring a .sol file or a full project directory.

    Args:
        path (str): path that was passed on the command line as the contract source

    Returns:
        bool: True if `path` is a file that looks like a solc Standard JSON input
    """
    if not path.endswith(".json") or not os.path.isfile(path):
        return False

    try:
        with open(path, encoding="utf8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return False

    return isinstance(data, dict) and all(key in data for key in _STANDARD_JSON_REQUIRED_KEYS)


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

    parser.add_argument(
        "--unstructured",
        action="store_true",
        help="Include unstructured storage slots",
    )

    parser.add_argument(
        "--include-immutable",
        action="store_true",
        help="Include immutable and constant variables in output",
    )

    cryticparser.init(parser)

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if len(args.contract_source) == 2:
        # Source code is file.sol, project directory, or a solc Standard JSON file
        source_code, target = args.contract_source
        kwargs = vars(args)
        if not kwargs.get("compile_force_framework") and _is_solc_standard_json(source_code):
            kwargs["compile_force_framework"] = "solc-json"
        slither = Slither(source_code, **kwargs)
    else:
        # Source code is published and retrieved via etherscan, or a solc Standard JSON file
        target = args.contract_source[0]
        kwargs = vars(args)
        if not kwargs.get("compile_force_framework") and _is_solc_standard_json(target):
            kwargs["compile_force_framework"] = "solc-json"
        slither = Slither(target, **kwargs)

    if args.contract_name:
        contracts = slither.get_contract_from_name(args.contract_name)
        if len(contracts) == 0:
            raise SlitherError(f"Contract {args.contract_name} not found.")
    else:
        contracts = slither.contracts

    rpc_info = None
    if args.rpc_url:
        valid = ["latest", "earliest", "pending", "safe", "finalized"]
        block = args.block if args.block in valid else int(args.block)
        rpc_info = RpcInfo(args.rpc_url, block)

    srs = SlitherReadStorage(contracts, args.max_depth, rpc_info)
    srs.unstructured = bool(args.unstructured)
    srs.include_immutable = bool(args.include_immutable)
    # Remove target prefix e.g. rinkeby:0x0 -> 0x0.
    address = target[target.find(":") + 1 :]
    # Default to implementation address unless a storage address is given.
    if not args.storage_address:
        args.storage_address = address
    srs.storage_address = args.storage_address

    if args.variable_name:
        # Use a lambda func to only return variables that have same name as target.
        # x is a StateVariable.
        srs.get_all_storage_variables(lambda x: bool(x.name == args.variable_name))
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
        with open(args.json, "w", encoding="utf8") as file:
            slot_infos_json = srs.to_json()
            json.dump(slot_infos_json, file, indent=4)


if __name__ == "__main__":
    main()
