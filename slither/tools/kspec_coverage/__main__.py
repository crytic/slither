import sys
import argparse
from slither import Slither
from .kspec_coverage import kspec_coverage
from crytic_compile import cryticparser

def parse_args():
    """
    Parse the underlying arguments for the program.
    :return: Returns the arguments for the program.
    """
    parser = argparse.ArgumentParser(description='kspec_coverage',
                                     usage='kspec_coverage contract kspec')

    parser.add_argument('contract', help='The filename of the contract or truffle directory to analyze.')
    parser.add_argument('kspec', help='The filename of the K spec proof(s) for the analyzed contract(s)')
    
    parser.add_argument('--version', help='displays the current version', version='0.1.0',action='version')

    cryticparser.init(parser) 
  
    if len(sys.argv) < 2: 
        parser.print_help(sys.stderr) 
        sys.exit(1)
     
    return parser.parse_args()


def main():
    # ------------------------------
    #       Usage: python3 -m kspec_coverage contract kspec
    #       Example: python3 -m kspec_coverage contract.sol kspec.md
    # ------------------------------
    # Parse all arguments

    args = parse_args()

    kspec_coverage(args)
    
if __name__ == '__main__':
    main()
