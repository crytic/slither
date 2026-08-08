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
    parser = ArgumentParser(
        description="Return contract functions based on the provided criteria.",
        usage="""
        Usage: slither-function-filter filename [flags]

        filename: The file path of the contract to be analyzed. 
        flags: Flag (or string input) to return matching functions.

        Flags:
        --contract-name (str):  Declared and inherited in the specified contract.
        --declared-only (bool): Only declared in the --contract-name.
        --visibility (str): Visibility of the functions.
        --modifiers (bool): Have modifiers.
        --ext-calls (bool): Make external calls.
        --int-calls (bool): Make internal calls.
        --state-change (bool): Change state.
        --read-only (bool): Do not change state.
        --contains-asm (bool): Contains inline assembly.
        --low-lvl-calls (bool): Make low level calls.
        --full-name (str): By their full name.
        --in-source (str): By the string in their source (use escape characters).
        """,
    )

    parser.add_argument("filename", help="The file path of the contract to be analyzed.")
    parser.add_argument(
        "--contract-name",
        type=str,
        help="Filter functions declared and inherited in the specified contract.",
    )
    parser.add_argument(
        "--declared-only",
        action="store_true",
        help="Filter only functions declared in the --contract-name.",
    )
    parser.add_argument("--visibility", type=str, help="Visibility of the functions.")
    parser.add_argument(
        "--modifiers", action="store_true", help="Filter functions that have modifiers."
    )
    parser.add_argument(
        "--ext-calls", action="store_true", help="Filter functions that make external calls."
    )
    parser.add_argument(
        "--int-calls", action="store_true", help="Filter functions that make internal calls."
    )
    parser.add_argument(
        "--state-change", action="store_true", help="Filter functions that change state."
    )
    parser.add_argument(
        "--read-only", action="store_true", help="Filter functions that do not change state."
    )
    parser.add_argument(
        "--contains-asm", action="store_true", help="Filter functions that contain inline assembly."
    )
    parser.add_argument(
        "--low-lvl-calls", action="store_true", help="Filter functions that make low level calls."
    )
    parser.add_argument("--full-name", type=str, help="Filter functions by their full name.")
    parser.add_argument(
        "--in-source", type=str, help="Filter functions by the string in their source."
    )

    cryticparser.init(parser)

    return parser.parse_args()


def filter_function(function: Function, args) -> bool:
    checks = [
        args.visibility and function.visibility != args.visibility,
        args.modifiers and not function.modifiers,
        args.ext_calls and not function.high_level_calls,
        args.int_calls and not function.internal_calls,
        args.state_change and (function.view or function.pure),
        args.read_only and not (function.view or function.pure),
        args.contains_asm and not function.contains_assembly,
        args.low_lvl_calls and not function.low_level_calls,
        args.full_name and args.full_name not in function.full_name,
        args.in_source and args.in_source not in function.source_mapping.content,
    ]
    return not any(checks)


def process_contract(contract, args):
    target_functions = contract.functions_declared if args.declared_only else contract.functions
    results = []
    for function in target_functions:
        if filter_function(function, args):
            lines = function.source_mapping.to_detailed_str().rsplit("(", 1)[0].strip()
            summary = function.get_summary() + (lines,)
            results.append(summary)
    return results


def main():
    args = parse_args()
    slither = Slither(args.filename, **vars(args))
    filter_results = []

    for contract in slither.contracts:
        if not args.contract_name or contract.name == args.contract_name:
            filter_results.extend(process_contract(contract, args))

    if filter_results:
        logger.info(f"Found {len(filter_results)} functions matching flags\n")
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
                lines,
            ) = result
            logger.info(bold(f"Function: {contract_name}.{function_sig}"))
            logger.info(bold(f"Reference: {lines}"))
            logger.info(blue(f"Visibility: {visibility}"))
            logger.info(blue(f"Modifiers: {modifiers}"))
            logger.info(blue(f"Variables Read: {vars_read}"))
            logger.info(blue(f"Variables Written: {vars_written}"))
            logger.info(blue(f"Internal Calls: {internal_calls}"))
            logger.info(blue(f"External Calls: {external_calls}"))
            logger.info(blue(f"Cyclomatic Complexity: {cyclomatic_complexity}\n"))
    else:
        logger.info("No functions matching flags found.")


if __name__ == "__main__":
    main()
