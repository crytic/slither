import argparse
import logging
from crytic_compile import cryticparser
from slither import Slither

logging.basicConfig()
logging.getLogger("Slither").setLevel(logging.INFO)

logger = logging.getLogger("Slither-demo")


def parse_args() -> argparse.Namespace:
    """
    Parse the underlying arguments for the program.
    :return: Returns the arguments for the program.
    """
    parser = argparse.ArgumentParser(description="Demo", usage="slither-demo filename")

    parser.add_argument(
        "filename", help="The filename of the contract or truffle directory to analyze."
    )

    # Add default arguments from crytic-compile
    cryticparser.init(parser)

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    # Perform slither analysis on the given filename
    _slither = Slither(args.filename, **vars(args))

    logger.info("Analysis done!")


if __name__ == "__main__":
    main()
