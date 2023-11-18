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

    # parser.add_argument(
    #     "--state-change", action="store_true", help="If set, filter functions that change state."
    # )

    cryticparser.init(parser)

    return parser.parse_args()


def filter_function(function: Function, args) -> dict[str, str]:
    summary = function.get_summary()

    data = {
        "contract_name": summary[0],
        "function_sig": summary[1],
        "visibility": summary[2],
        "modifiers": summary[3],
        "vars_read": summary[4],
        "vars_written": summary[5],
        "internal_calls": summary[6],
        "external_calls": summary[7],
        "cyclomatic_complexity": summary[8],
        "flags" : []
        # "flags": {
        #     "visibility": False,
        #     "modifiers": False,
        #     "ext-calls": False,
        #     "int-calls": False,
        # },
    }

    # Check visibility
    if args.visibility and function.visibility != args.visibility:
        data["flags"].append(True)
        # data["flags"]["visibility"] = True

    # Check for modifiers
    if args.modifiers:
        if data["modifiers"] is not None:
            data["flags"]["modifiers"] = True

    # Check for external calls
    if args.ext_calls:
        if data["external_calls"] is not None:
            data["flags"]["ext-calls"] = True

    # Check for internal calls
    if args.int_calls:
        if data["internal_calls"] is not None:
            data["flags"]["int-calls"] = True


def main() -> None:
    args = parse_args()

    # Perform slither analysis on the given filename
    slither = Slither(args.filename, **vars(args))

    # Access the arguments
    contract_name = args.contract_name
    # Store list
    args_list = [args.visibility, args.modifiers, args.ext_calls, args.int_calls]
    filter_results = []

    for contract in slither.contracts:
        # Scan only target contract's functions (declared and inherited)
        if contract.name == contract_name:
            # Find directly inherited contracts
            contracts_inherited = [
                parent for parent in contract.immediate_inheritance if not parent.is_interface
            ]

            # Iterate declared functions
            for function in contract.functions:
                # data = function_matches_criteria(function, args)
                filter_results.append(filter_function(function, args))

            # Iterate inherited functions
            for function in contracts_inherited:
                filter_results.append(filter_function(function, args))

        # Scan everything if no target contract is specified
        if not contract_name:
            for function in contract.functions:
                filter_results.append(filter_function(function, args))

    for target in filter_results[:]:
        # Check if any of the flags is False and its corresponding arg is set
        if (args.visibility and not target["flags"]["visibility"]) or \
           (args.modifiers and not target["flags"]["modifiers"]) or \
           (args.ext_calls and not target["flags"]["ext-calls"]) or \
           (args.int_calls and not target["flags"]["int-calls"]):
            filter_results.remove(target)
    
    print(filter_results)
    

if __name__ == "__main__":
    main()
