import sys
import logging
from argparse import ArgumentParser, Namespace

from crytic_compile import cryticparser
from slither import Slither
from slither.core.declarations import Function
from slither.utils.colors import green

logging.basicConfig()
logging.getLogger("Slither").setLevel(logging.INFO)


def parse_args() -> Namespace:
    """
    Parse the underlying arguments for the program.
    :return: Returns the arguments for the program.
    """
    parser: ArgumentParser = ArgumentParser(
        description="FunctionSummarySelection",
        usage="function_summary_selection.py filename [options]",
    )

    parser.add_argument(
        "filename", help="The filename of the contract or truffle directory to analyze."
    )

    parser.add_argument(
        "--contract-name", type=str, help="If set, filter functions declared only in that contract."
    )

    parser.add_argument("--visibility", type=str, help="Visibility of the functions.")

    parser.add_argument(
        "--modifiers", action="store_true", help="If set, filter functions that have modifiers."
    )

    parser.add_argument(
        "--ext-calls",
        action="store_true",
        help="If set, filter functions that make external calls.",
    )

    parser.add_argument(
        "--int-calls",
        action="store_true",
        help="If set, filter functions that make internal calls.",
    )

    parser.add_argument(
        "--state-change", action="store_true", help="If set, filter functions that change state."
    )

    cryticparser.init(parser)

    return parser.parse_args()


def main() -> None:
    # ------------------------------
    # FunctionSummarySelection.py
    #       Usage: python3 function_summary_selection.py filename [options]
    #       Example: python3 function_summary_selection.py contract.sol ----
    # ------------------------------
    args = parse_args()

    # Perform slither analysis on the given filename
    # args's empty
    slither = Slither(args.filename, **vars(args))

    # Access the arguments
    contract_name = args.contract_name
    visibility = args.visibility
    modifiers = args.modifiers
    ext_calls = args.ext_calls
    int_calls = args.int_calls
    state_change = args.state_change

    for contract in slither.contracts:
        if contract.name == contract_name:
            # get all contracts for target contract, drop interfaces
            contracts_inherited = [
                parent for parent in contract.immediate_inheritance if not parent.is_interface
            ]

            for function in contract.functions:
                print("contract.name == contract_name, contract.functions", function.name)

            for function in contracts_inherited:
                print(
                    "contract.name == contract_name, function in contracts_inherited", function.name
                )

        else:
            for function in contract.functions:
                print("contract.name != contract_name", function.name)

    # # Extract function summaries based on selected options
    # function_summaries = summarize_functions(slither, args.options if args.options else range(1, 8))

    # # Output the function summaries
    # for function_summary in function_summaries:
    #     print(green(function_summary))

    print("\n")


if __name__ == "__main__":
    main()
