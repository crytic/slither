import sys
import logging
import argparse
from crytic_compile import cryticparser
from slither.tools.kspec_coverage.kspec_coverage import kspec_coverage

logging.basicConfig()
logger = logging.getLogger("Slither.kspec")
logger.setLevel(logging.INFO)

ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter("%(message)s")
logger.addHandler(ch)
logger.handlers[0].setFormatter(formatter)
logger.propagate = False


def parse_args() -> argparse.Namespace:
    """
    Parse the underlying arguments for the program.
    :return: Returns the arguments for the program.
    """
    parser = argparse.ArgumentParser(
        description="slither-kspec-coverage",
        usage="slither-kspec-coverage contract.sol kspec.md",
    )

    parser.add_argument(
        "contract", help="The filename of the contract or truffle directory to analyze."
    )
    parser.add_argument(
        "kspec",
        help="The filename of the Klab spec markdown for the analyzed contract(s)",
    )

    parser.add_argument(
        "--version",
        help="displays the current version",
        version="0.1.0",
        action="version",
    )
    parser.add_argument(
        "--json",
        help='Export the results as a JSON file ("--json -" to export to stdout)',
        action="store",
        default=False,
    )

    cryticparser.init(parser)

    if len(sys.argv) < 2:
        parser.print_help(sys.stderr)
        sys.exit(1)

    return parser.parse_args()


def main() -> None:
    # ------------------------------
    #       Usage: slither-kspec-coverage contract kspec
    #       Example: slither-kspec-coverage contract.sol kspec.md
    # ------------------------------
    # Parse all arguments

    args = parse_args()

    kspec_coverage(args)


if __name__ == "__main__":
    main()
