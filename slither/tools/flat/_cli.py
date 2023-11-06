from argparse import ArgumentParser
from crytic_compile.utils.zip import ZIP_TYPES_ACCEPTED

from slither.tools.flat.flattening import Strategy, STRATEGIES_NAMES, DEFAULT_EXPORT_PATH


def init_parser(sub_parser: ArgumentParser) -> None:
    """Parse the underlying arguments for the program.
    Returns:
        The arguments for the program.
    """
    parser = sub_parser.add_parser(
        name="flat",
        help="Contracts flattening. See https://github.com/crytic/slither/wiki/Contract-Flattening",
    )

    # parser.add_argument("filename", help="The filename of the contract or project to analyze.") # TODO remove?

    parser.add_argument("--contract", help="Flatten one contract.", default=None)

    parser.add_argument(
        "--strategy",
        help=f"Flatenning strategy: {STRATEGIES_NAMES} (default: MostDerived).",
        default=Strategy.MostDerived.name,  # pylint: disable=no-member
    )

    group_export = parser.add_argument_group("Export options")

    group_export.add_argument(
        "--dir",
        help=f"Export directory (default: {DEFAULT_EXPORT_PATH}).",
        default=None,
    )

    group_export.add_argument(
        "--json",
        help='Export the results as a JSON file ("--json -" to export to stdout)',
        action="store",
        default=None,
    )

    parser.add_argument(
        "--zip",
        help="Export all the files to a zip file",
        action="store",
        default=None,
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
        "--convert-private",
        help="Convert private variables to internal.",
        action="store_true",
    )

    group_patching.add_argument(
        "--convert-library-to-internal",
        help="Convert external or public functions to internal in library.",
        action="store_true",
    )

    group_patching.add_argument(
        "--remove-assert", help="Remove call to assert().", action="store_true"
    )

    group_patching.add_argument(
        "--pragma-solidity",
        help="Set the solidity pragma with a given version.",
        action="store",
        default=None,
    )
