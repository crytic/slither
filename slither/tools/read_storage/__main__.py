import argparse
import logging
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.core.solidity_types.array_type import ArrayType

from web3 import Web3
from crytic_compile import cryticparser, CryticCompile, InvalidCompilation

from slither import Slither
from slither.tools.read_storage.read_storage import convert_hex_bytes_to_type, get_offset_value

logging.basicConfig()
logger = logging.getLogger("Slither")
logger.setLevel(logging.INFO)


def parse_args():
    """
    Parse the underlying arguments for the program.
    :return: Returns the arguments for the program.
    """
    parser = argparse.ArgumentParser(
        description="Read a variable's value from storage for a deployed contract",
        usage="slither-read-storage [codebase] address canonical_variable_name",
    )

    parser.add_argument(
        "contract_source",
        help="The deployed contract address on mainnet and project directory for unverified contracts",
        nargs="+",
    )

    parser.add_argument(
        "canonical_variable_name",
        help="The name of the variable whose value will be returned",
    )

    parser.add_argument(
        "--key", 
        help="The index or key whose value will be returned from a mapping",
        default=0
    )

    parser.add_argument(
        "--rpc-url",
        help="An endpoint for web3 requests"
    )

    parser.add_argument(
        "--print-all",
        help="Print all non-constant variable values"
    )

    cryticparser.init(parser)

    return parser.parse_args()


def main():
    args = parse_args()
    print(args.contract_source)
    if len(args.contract_source) == 2:
        source_code, address = args.contract_source  # Source code is file .sol, project directory
        slither = Slither(source_code, **vars(args))
    else:
        address = args.contract_source[0]  # Source code is open source and retrieved via etherscan
        slither = Slither(address, **vars(args))

    for contract in slither.contracts_derived:
        # Find all instances of the variable in the target contract(s)
        if args.canonical_variable_name in contract.variables_as_dict:
            target_variable = contract.variables_as_dict[args.canonical_variable_name]
            if (
                target_variable.is_constant
            ):  # Variable may exist in multiple contracts so continue rather than raising exception
                print("The solidity compiler does not reserve storage for constants")
                continue
            try:
                size, requires_new_slot = target_variable.type.storage_size
                print(f"storage size {size}\n requires new slot {requires_new_slot}")
                print(type(target_variable.type))
                if isinstance(target_variable.type, ElementaryType):
                    print(f"size {target_variable.type.size}")
                (slot, offset) = contract.compilation_unit.storage_layout_of(
                    contract, target_variable
                )
                if args.key:
                    slot += int(args.key)

                print(requires_new_slot)
                web3 = Web3(Web3.HTTPProvider(args.rpc_url))
                checksum_address = web3.toChecksumAddress(address)
                hex_bytes = web3.eth.get_storage_at(checksum_address, slot)
                print(
                    f"\n{target_variable.canonical_name} with type {target_variable.type} evaluated to:\n{(hex_bytes.hex())}\nin contract '{contract.name}' at storage slot: {slot}"
                )
                if size < 32:
                    hex_bytes = get_offset_value(hex_bytes, offset, size)

                if isinstance(target_variable.type, ArrayType):
                    name = target_variable.type.type.name
                else:
                    name = target_variable.type.name
                # if target_variable.type
                print(f"\n{name} value: {convert_hex_bytes_to_type(web3, hex_bytes, name)}")
            except KeyError:  # Only the child contract of a parent contract will show up in the storage layout when inheritance is used
                print(
                    f"Contract {contract} not found in storage layout. It is possibly a parent contract"
                )


if __name__ == "__main__":
    main()
