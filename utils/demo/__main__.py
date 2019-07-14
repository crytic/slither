import os
import argparse
import logging
from slither import Slither
from crytic_compile import cryticparser

logging.basicConfig()
logging.getLogger("Slither").setLevel(logging.INFO)

logger = logging.getLogger("Slither-demo")

def parse_args():
    """
    Parse the underlying arguments for the program.
    :return: Returns the arguments for the program.
    """
    parser = argparse.ArgumentParser(description='Demo',
                                     usage='slither-demo filename')

    parser.add_argument('filename',
                        help='The filename of the contract or truffle directory to analyze.')

    # Add default arguments from crytic-compile
    cryticparser.init(parser)

    return parser.parse_args()


def main():
    args = parse_args()

    # Perform slither analysis on the given filename
    slither = Slither(args.filename, **vars(args))

    logger.info('Analysis done!')

if __name__ == '__main__':
    main()
