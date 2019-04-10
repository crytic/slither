import os
import argparse
from slither import Slither
from slither.utils.colors import red
import logging
from .slither_format import slither_format

logging.basicConfig()
logging.getLogger("Slither").setLevel(logging.INFO)

def parse_args():
    """
    Parse the underlying arguments for the program.
    :return: Returns the arguments for the program.
    """
    parser = argparse.ArgumentParser(description='slither_format',
                                     usage='slither_format filename')

    parser.add_argument('filename',
                        help='The filename of the contract or truffle directory to analyze.')

    parser.add_argument('--solc', help='solc path', default='solc')

    return parser.parse_args()


def main():
    # ------------------------------
    #       Usage: python3 -m slither_format filename
    #       Example: python3 -m slither_format contract.sol
    # ------------------------------
    # Parse all arguments
    args = parse_args()

    # Perform slither analysis on the given filename
    slither = Slither(args.filename, is_truffle=os.path.isdir(args.filename), solc=args.solc, disable_solc_warnings=True)

    # Format the input files based on slither analysis
    slither_format(slither)

if __name__ == '__main__':
    main()
