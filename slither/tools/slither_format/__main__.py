import sys
import argparse
import logging
from crytic_compile import cryticparser
from slither import Slither
from slither.utils.command_line import read_config_file
from slither.tools.slither_format.slither_format import slither_format


logging.basicConfig()
logging.getLogger("Slither").setLevel(logging.INFO)

# Slither detectors for which slither-format currently works
available_detectors = [
    "unused-state",
    "solc-version",
    "pragma",
    "naming-convention",
    "external-function",
    "constable-states",
    "constant-function-asm",
    "constatnt-function-state",
]


def parse_args() -> argparse.Namespace:
    """
    Parse the underlying arguments for the program.
    :return: Returns the arguments for the program.
    """
    parser = argparse.ArgumentParser(description="slither_format", usage="slither_format filename")

    parser.add_argument(
        "filename", help="The filename of the contract or truffle directory to analyze."
    )
    parser.add_argument(
        "--verbose-test",
        "-v",
        help="verbose mode output for testing",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "--verbose-json",
        "-j",
        help="verbose json output",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "--version",
        help="displays the current version",
        version="0.1.0",
        action="version",
    )

    parser.add_argument(
        "--config-file",
        help="Provide a config file (default: slither.config.json)",
        action="store",
        dest="config_file",
        default="slither.config.json",
    )

    group_detector = parser.add_argument_group("Detectors")
    group_detector.add_argument(
        "--detect",
        help="Comma-separated list of detectors, defaults to all, "
        f"available detectors: {', '.join(d for d in available_detectors)}",
        action="store",
        dest="detectors_to_run",
        default="all",
    )

    group_detector.add_argument(
        "--exclude",
        help="Comma-separated list of detectors to exclude,"
        "available detectors: {', '.join(d for d in available_detectors)}",
        action="store",
        dest="detectors_to_exclude",
        default="all",
    )

    cryticparser.init(parser)

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    return parser.parse_args()


def main() -> None:
    # ------------------------------
    #       Usage: python3 -m slither_format filename
    #       Example: python3 -m slither_format contract.sol
    # ------------------------------
    # Parse all arguments
    args = parse_args()

    read_config_file(args)

    # Perform slither analysis on the given filename
    slither = Slither(args.filename, **vars(args))

    # Format the input files based on slither analysis
    slither_format(slither, **vars(args))


if __name__ == "__main__":
    main()
