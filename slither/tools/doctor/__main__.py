import argparse
import logging

from crytic_compile import cryticparser


logging.basicConfig()
logging.getLogger("Slither").setLevel(logging.INFO)

logger = logging.getLogger("Slither-doctor")
logger.setLevel(logging.INFO)

ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter("%(message)s")
logger.addHandler(ch)
logger.handlers[0].setFormatter(formatter)
logger.propagate = False


def parse_args():
    """
    Parse the underlying arguments for the program.
    :return: Returns the arguments for the program.
    """
    parser = argparse.ArgumentParser(
        description="Troubleshoot running Slither on your project",
        usage="slither-doctor project",
    )

    parser.add_argument("project", help="The codebase to be tested.")

    # Add default arguments from crytic-compile
    cryticparser.init(parser)

    return parser.parse_args()


def main():
    args = parse_args()

    print("Hello world")


if __name__ == "__main__":
    main()
