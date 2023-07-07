import argparse
import logging
from pathlib import Path

from crytic_compile import cryticparser

from slither import Slither
from slither.utils.code_generation import generate_interface

logging.basicConfig()
logger = logging.getLogger("Slither-Interface")
logger.setLevel(logging.INFO)


def parse_args() -> argparse.Namespace:
    """
    Parse the underlying arguments for the program.
    :return: Returns the arguments for the program.
    """
    parser = argparse.ArgumentParser(
        description="Generates code for a Solidity interface from contract",
        usage=("slither-interface <ContractName> <source file or deployment address>"),
    )

    parser.add_argument(
        "contract_source",
        help="The name of the contract (case sensitive) followed by the deployed contract address if verified on etherscan or project directory/filename for local contracts.",
        nargs="+",
    )

    parser.add_argument(
        "--unroll-structs",
        help="Whether to use structures' underlying types instead of the user-defined type",
        default=False,
        action="store_true",
    )

    parser.add_argument(
        "--exclude-events",
        help="Excludes event signatures in the interface",
        default=False,
        action="store_true",
    )

    parser.add_argument(
        "--exclude-errors",
        help="Excludes custom error signatures in the interface",
        default=False,
        action="store_true",
    )

    parser.add_argument(
        "--exclude-enums",
        help="Excludes enum definitions in the interface",
        default=False,
        action="store_true",
    )

    parser.add_argument(
        "--exclude-structs",
        help="Exclude struct definitions in the interface",
        default=False,
        action="store_true",
    )

    cryticparser.init(parser)

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    contract_name, target = args.contract_source
    slither = Slither(target, **vars(args))

    _contract = slither.get_contract_from_name(contract_name)[0]

    interface = generate_interface(
        contract=_contract,
        unroll_structs=args.unroll_structs,
        include_events=not args.exclude_events,
        include_errors=not args.exclude_errors,
        include_enums=not args.exclude_enums,
        include_structs=not args.exclude_structs,
    )

    # add version pragma
    if _contract.compilation_unit.pragma_directives:
        interface = (
            f"pragma solidity {_contract.compilation_unit.pragma_directives[0].version};\n\n"
            + interface
        )

    # write interface to file
    export = Path("crytic-export", "interfaces")
    export.mkdir(parents=True, exist_ok=True)
    filename = f"I{contract_name}.sol"
    path = Path(export, filename)
    logger.info(f" Interface exported to {path}")
    with open(path, "w", encoding="utf8") as f:
        f.write(interface)


if __name__ == "__main__":
    main()
