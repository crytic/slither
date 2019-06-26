import os, sys
import argparse
from slither import Slither
from slither.utils.colors import red
import logging
from .slither_format import slither_format
from crytic_compile import cryticparser

logging.basicConfig()
logging.getLogger("Slither").setLevel(logging.INFO)

# Slither detectors for which slither-format currently works
available_detectors = ["unused-state",
                       "solc-version",
                       "pragma",
                       "naming-convention",
                       "external-function",
                       "constable-states",
                       "constant-function"]

detectors_to_run = []

def parse_args():
    """
    Parse the underlying arguments for the program.
    :return: Returns the arguments for the program.
    """
    parser = argparse.ArgumentParser(description='slither_format',
                                     usage='slither_format filename')

    parser.add_argument('filename', help='The filename of the contract or truffle directory to analyze.')
    parser.add_argument('--verbose-test', '-v', help='verbose mode output for testing',action='store_true',default=False)
    parser.add_argument('--verbose-json', '-j', help='verbose json output',action='store_true',default=False)
    parser.add_argument('--version',
                        help='displays the current version',
                        version='0.1.0',
                        action='version')

    parser.add_argument('--skip-patch-generation',
                        help='Do not generate patch files',
                        action='store_true',
                        default=False)
    
    group_detector = parser.add_argument_group('Detectors')
    group_detector.add_argument('--detect',
                                help='Comma-separated list of detectors, defaults to all, '
                                'available detectors: {}'.format(
                                    ', '.join(d for d in available_detectors)),
                                action='store',
                                dest='detectors_to_run',
                                default='all')

    cryticparser.init(parser) 
  
    if len(sys.argv) == 1: 
        parser.print_help(sys.stderr) 
        sys.exit(1)
     
    return parser.parse_args()


def main():
    # ------------------------------
    #       Usage: python3 -m slither_format filename
    #       Example: python3 -m slither_format contract.sol
    # ------------------------------
    # Parse all arguments
    args = parse_args()

    # Perform slither analysis on the given filename
    slither = Slither(args.filename, **vars(args))

    # Format the input files based on slither analysis
    slither_format(slither, **vars(args))
if __name__ == '__main__':
    main()
