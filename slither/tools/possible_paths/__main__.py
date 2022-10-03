import sys

import logging
from argparse import ArgumentParser, Namespace

from crytic_compile import cryticparser
from slither import Slither
from slither.core.declarations import FunctionContract
from slither.utils.colors import red
from slither.tools.possible_paths.possible_paths import (
    find_target_paths,
    resolve_functions,
    ResolveFunctionException,
)

logging.basicConfig()
logging.getLogger("Slither").setLevel(logging.INFO)


def parse_args() -> Namespace:
    """
    Parse the underlying arguments for the program.
    :return: Returns the arguments for the program.
    """
    parser: ArgumentParser = ArgumentParser(
        description="PossiblePaths",
        usage="possible_paths.py filename [contract.function targets]",
    )

    parser.add_argument(
        "filename", help="The filename of the contract or truffle directory to analyze."
    )

    parser.add_argument("targets", nargs="+")

    cryticparser.init(parser)

    return parser.parse_args()


def main() -> None:
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
    except ResolveFunctionException as resolvefunction:
        print(red(resolvefunction))
        sys.exit(-1)

    # Print out all target functions.
    print("Target functions:")
    for target in targets:
        if isinstance(target, FunctionContract):
            print(f"- {target.contract_declarer.name}.{target.full_name}")
        else:
            pass
            # TODO implement me
    print("\n")

    # Obtain all paths which reach the target functions.
    reaching_paths = find_target_paths(slither, targets)
    reaching_functions = {y for x in reaching_paths for y in x if y not in targets}

    # Print out all function names which can reach the targets.
    print("The following functions reach the specified targets:")
    for function_desc in sorted([f"{f.canonical_name}" for f in reaching_functions]):
        print(f"- {function_desc}")
    print("\n")

    # Format all function paths.
    reaching_paths_str = [
        " -> ".join([f"{f.canonical_name}" for f in reaching_path])
        for reaching_path in reaching_paths
    ]

    # Print a sorted list of all function paths which can reach the targets.
    print("The following paths reach the specified targets:")
    for reaching_path in sorted(reaching_paths_str):
        print(f"{reaching_path}\n")


if __name__ == "__main__":
    main()
