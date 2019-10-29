import sys
import argparse
from slither import Slither
from slither.utils.command_line import read_config_file
import logging
from .kspec_coverage import kspec_coverage
from crytic_compile import cryticparser

logging.basicConfig()
logger = logging.getLogger("Slither").setLevel(logging.INFO)

def parse_args():
    """
    Parse the underlying arguments for the program.
    :return: Returns the arguments for the program.
    """
    parser = argparse.ArgumentParser(description='kspec_coverage',
                                     usage='kspec_coverage filename -k kproof')

    parser.add_argument('filename', help='The filename of the contract or truffle directory to analyze.')
    parser.add_argument('--kspec-proof', '-k', help='The filename of the K spec proof for the analyzed contracts')
    parser.add_argument('--verbose-test', '-v', help='verbose mode output for testing',action='store_true',default=False)
    parser.add_argument('--verbose-json', '-j', help='verbose json output',action='store_true',default=False)
    parser.add_argument('--version',
                        help='displays the current version',
                        version='0.1.0',
                        action='version')

    cryticparser.init(parser) 
  
    if len(sys.argv) < 3: 
        parser.print_help(sys.stderr) 
        sys.exit(1)
     
    return parser.parse_args()


def main():
    # ------------------------------
    #       Usage: python3 -m kspec_coverage filename -k kproof
    #       Example: python3 -m kspec_coverage contract.sol -k kproof.txt
    # ------------------------------
    # Parse all arguments

    args = parse_args()

    kspec_coverage(args)
    
if __name__ == '__main__':
    main()
