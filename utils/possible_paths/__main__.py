import os
import argparse
from slither import Slither
from slither.utils.colors import red
import logging
from .possible_paths import find_target_paths, resolve_functions, ResolveFunctionException
from crytic_compile import cryticparser

logging.basicConfig()
logging.getLogger("Slither").setLevel(logging.INFO)

def parse_args():
    """
    Parse the underlying arguments for the program.
    :return: Returns the arguments for the program.
    """
    parser = argparse.ArgumentParser(description='PossiblePaths',
                                     usage='possible_paths.py filename [contract.function targets]')

    parser.add_argument('filename',
                        help='The filename of the contract or truffle directory to analyze.')

    parser.add_argument('targets', nargs='+')

    cryticparser.init(parser)

    return parser.parse_args()


def main():
    # ------------------------------
    # PossiblePaths.py
    #       Usage: python3 possible_paths.py filename targets
    #       Example: python3 possible_paths.py contract.sol contract1.function1 contract2.function2 contract3.function3
    # ------------------------------
    # Parse all arguments
    args = parse_args()

    # Perform slither analysis on the given filename
    slither = Slither(args.filename, **vars(args))

    try:
        targets = resolve_functions(slither, args.targets)
    except ResolveFunctionException as r:
        print(red(r))
        exit(-1)

    # Print out all target functions.
    print(f"Target functions:")
    for target in targets:
        print(f"- {target.contract_declarer.name}.{target.full_name}")
    print("\n")

    # Obtain all paths which reach the target functions.
    reaching_paths = find_target_paths(slither, targets)
    reaching_functions = set([y for x in reaching_paths for y in x if y not in targets])

    # Print out all function names which can reach the targets.
    print(f"The following functions reach the specified targets:")
    for function_desc in sorted([f"{f.canonical_name}" for f in reaching_functions]):
        print(f"- {function_desc}")
    print("\n")

    # Format all function paths.
    reaching_paths_str = [' -> '.join([f"{f.canonical_name}" for f in reaching_path]) for reaching_path in reaching_paths]

    # Print a sorted list of all function paths which can reach the targets.
    print(f"The following paths reach the specified targets:")
    for reaching_path in sorted(reaching_paths_str):
        print(f"{reaching_path}\n")

if __name__ == '__main__':
    main()
