import argparse
import logging
import sys

from crytic_compile import cryticparser
from crytic_compile.utils.zip import ZIP_TYPES_ACCEPTED

from slither import Slither
from slither.tools.flattening.flattening import (
    Flattening,
    Strategy,
    STRATEGIES_NAMES,
    DEFAULT_EXPORT_PATH,
)

logging.basicConfig()
logger = logging.getLogger("Slither")
logger.setLevel(logging.INFO)


def parse_args():
    """
    Parse the underlying arguments for the program.
    :return: Returns the arguments for the program.
    """
    parser = argparse.ArgumentParser(
        description="Contracts flattening. See https://github.com/crytic/slither/wiki/Contract-Flattening",
        usage="slither-flat filename",
    )

    parser.add_argument("filename", help="The filename of the contract or project to analyze.")

    parser.add_argument("--contract", help="Flatten one contract.", default=None)

    parser.add_argument(
        "--strategy",
        help=f"Flatenning strategy: {STRATEGIES_NAMES} (default: MostDerived).",
        default=Strategy.MostDerived.name,
    )

    group_export = parser.add_argument_group("Export options")

    group_export.add_argument(
        "--dir", help=f"Export directory (default: {DEFAULT_EXPORT_PATH}).", default=None
    )

    group_export.add_argument(
        "--json",
        help='Export the results as a JSON file ("--json -" to export to stdout)',
        action="store",
        default=None,
    )

    parser.add_argument(
        "--zip", help="Export all the files to a zip file", action="store", default=None,
    )

    parser.add_argument(
        "--zip-type",
        help=f"Zip compression type. One of {','.join(ZIP_TYPES_ACCEPTED.keys())}. Default lzma",
        action="store",
        default=None,
    )

    group_patching = parser.add_argument_group("Patching options")

    group_patching.add_argument(
        "--convert-external", help="Convert external to public.", action="store_true"
    )

    group_patching.add_argument(
        "--convert-private", help="Convert private variables to internal.", action="store_true"
    )

    group_patching.add_argument(
        "--remove-assert", help="Remove call to assert().", action="store_true"
    )

    group_patching.add_argument(
        "--pragma-solidity", help="For a given solidity version.", action="store", default=None
    )

    # Add default arguments from crytic-compile
    cryticparser.init(parser)

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    return parser.parse_args()


def main():
    args = parse_args()

    slither = Slither(args.filename, **vars(args))
    flat = Flattening(
        slither,
        external_to_public=args.convert_external,
        remove_assert=args.remove_assert,
        private_to_internal=args.convert_private,
        export_path=args.dir,
        pragma_solidity=args.pragma_solidity
    )

    try:
        strategy = Strategy[args.strategy]
    except KeyError:
        logger.error(
            f"{args.strategy} is not a valid strategy, use: {STRATEGIES_NAMES} (default MostDerived)"
        )
        return
    flat.export(
        strategy=strategy,
        target=args.contract,
        json=args.json,
        zip=args.zip,
        zip_type=args.zip_type,
    )


if __name__ == "__main__":
    main()
