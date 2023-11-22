import logging
from argparse import ArgumentParser, Namespace

from crytic_compile import cryticparser
from slither import Slither
from slither.core.declarations import Function
from slither.utils.colors import green, blue, red, bold

logging.basicConfig()
logger = logging.getLogger("Slither-function-filter")
logger.setLevel(logging.INFO)


def parse_args() -> Namespace:
    """
    Parse the underlying arguments for the program.
    :return: Returns the arguments for the program.
    """
    parser: ArgumentParser = ArgumentParser(
        description="Return contract functions based on the provided criteria.",
        usage="slither-function-filter filename [options]",
    )

    parser.add_argument(
        "filename", help="The filename of the contract or truffle directory to analyze."
    )

    parser.add_argument(
        "--contract-name",
        type=str,
        help="If set, filter functions declared and inherited in the specified contract.",
    )

    parser.add_argument(
        "--declared-only",
        action="store_true",
        help="If set, filter functions only declared in the --contract-name.",
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

    parser.add_argument(
        "--read-only",
        action="store_true",
        help="If set, filter functions that do not change state.",
    )

    cryticparser.init(parser)

    return parser.parse_args()


def filter_function(function: Function, args) -> bool:
    # Check visibility
    if args.visibility and function.visibility != args.visibility:
        return False

    # Check for existence of modifiers
    if args.modifiers:
        if not function.modifiers:
            return False

    # Check for existence of external calls
    if args.ext_calls:
        if not function.high_level_calls:
            return False

    # Check for existence of internal calls
    if args.int_calls:
        if not function.internal_calls:
            return False

    # Check if function potentially changes state
    if args.state_change:
        if function.view or function.pure:
            return False

    # Check if function is read-only
    if args.read_only:
        if not (function.view or function.pure):
            return False

    # If none of the conditions have returned False, the function matches all provided criteria
    return True


def main() -> None:
    args = parse_args()

    # Perform slither analysis on the given filename
    slither = Slither(args.filename, **vars(args))

    # Access the arguments
    contract_name = args.contract_name
    # Store list
    filter_results = []

    for contract in slither.contracts:
        # Scan only target contract's functions (declared and inherited)
        if contract_name:
            # Match --contract-name with slither's contract object
            if contract.name == contract_name:
                # Only target contract's declared functions are scanned
                if args.declared_only:
                    # Iterate declared functions
                    for function in contract.functions:
                        if filter_function(function, args):
                            filter_results.append(function.get_summary())

                # All functions (declared and inherited) are scanned
                else:
                    contracts_inherited = [
                        parent
                        for parent in contract.immediate_inheritance
                        if not parent.is_interface
                    ]

                    # Iterate declared functions
                    for function in contract.functions:
                        if filter_function(function, args):
                            filter_results.append(function.get_summary())

                    # Iterate inherited functions
                    for contracts in contracts_inherited:
                        for function in contracts.functions:
                            if filter_function(function, args):
                                filter_results.append(function.get_summary())

        # Scan all contracts in the SourceMapping of filename provided
        else:
            for function in contract.functions:
                if filter_function(function, args):
                    filter_results.append(function.get_summary())

    if filter_results:
        logger.info(green(f"Found {len(filter_results)} functions matching flags\n"))
        for result in filter_results:
            (
                contract_name,
                function_sig,
                visibility,
                modifiers,
                vars_read,
                vars_written,
                internal_calls,
                external_calls,
                cyclomatic_complexity,
            ) = result

            logger.info(bold(f"Function: {contract_name}.{function_sig}"))
            logger.info(blue(f"Visibility: {visibility}"))
            logger.info(blue(f"Modifiers: {modifiers}"))
            logger.info(blue(f"Variables Read: {vars_read}"))
            logger.info(blue(f"Variables Written: {vars_written}"))
            logger.info(blue(f"Internal Calls: {internal_calls}"))
            logger.info(blue(f"External Calls: {external_calls}"))
            logger.info(blue(f"Cyclomatic Complexity: {cyclomatic_complexity}\n"))
    else:
        logger.info(red("No functions matching flags found."))


if __name__ == "__main__":
    main()
