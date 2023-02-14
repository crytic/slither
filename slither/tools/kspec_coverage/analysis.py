import logging
import re
from argparse import Namespace
from typing import Set, Tuple, List, Dict, Union, Optional, Callable

from slither.core.compilation_unit import SlitherCompilationUnit
from slither.core.declarations import FunctionContract
from slither.core.variables.state_variable import StateVariable
from slither.utils import output
from slither.utils.colors import yellow, green, red

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("Slither.kspec")


# pylint: disable=anomalous-backslash-in-string


def _refactor_type(targeted_type: str) -> str:
    return {"uint": "uint256", "int": "int256"}.get(targeted_type, targeted_type)


def _get_all_covered_kspec_functions(target: str) -> Set[Tuple[str, str]]:
    # Create a set of our discovered functions which are covered
    covered_functions: Set[Tuple[str, str]] = set()

    BEHAVIOUR_PATTERN = re.compile(r"behaviour\s+(\S+)\s+of\s+(\S+)")
    INTERFACE_PATTERN = re.compile(r"interface\s+([^\r\n]+)")

    # Read the file contents
    with open(target, "r", encoding="utf8") as target_file:
        lines = target_file.readlines()

    # Loop for each line, if a line matches our behaviour regex, and the next one matches our interface regex,
    # we add our finding
    i = 0
    while i < len(lines):
        match = BEHAVIOUR_PATTERN.match(lines[i])
        if match:
            contract_name = match.groups()[1]
            match = INTERFACE_PATTERN.match(lines[i + 1])
            if match:
                function_full_name = match.groups()[0]
                start, end = (
                    function_full_name.index("(") + 1,
                    function_full_name.index(")"),
                )
                function_arguments = function_full_name[start:end].split(",")
                function_arguments = [
                    _refactor_type(arg.strip().split(" ")[0]) for arg in function_arguments
                ]
                function_full_name = function_full_name[:start] + ",".join(function_arguments) + ")"
                covered_functions.add((contract_name, function_full_name))
                i += 1
        i += 1
    return covered_functions


def _get_slither_functions(
    slither: SlitherCompilationUnit,
) -> Dict[Tuple[str, str], Union[FunctionContract, StateVariable]]:
    # Use contract == contract_declarer to avoid dupplicate
    all_functions_declared: List[Union[FunctionContract, StateVariable]] = [
        f
        for f in slither.functions
        if (
            (isinstance(f, FunctionContract) and f.contract == f.contract_declarer)
            and f.is_implemented
            and not f.is_constructor
            and not f.is_constructor_variables
        )
    ]
    # Use list(set()) because same state variable instances can be shared accross contracts
    # TODO: integrate state variables
    all_functions_declared += list(
        {s for s in slither.state_variables if s.visibility in ["public", "external"]}
    )
    slither_functions = {
        (function.contract.name, function.full_name): function
        for function in all_functions_declared
    }

    return slither_functions


def _generate_output(
    kspec: List[Union[FunctionContract, StateVariable]],
    message: str,
    color: Callable[[str], str],
    generate_json: bool,
) -> Optional[Dict]:
    info = ""
    for function in kspec:
        info += f"{message} {function.contract.name}.{function.full_name}\n"
    if info:
        logger.info(color(info))

    if generate_json:
        json_kspec_present = output.Output(info)
        for function in kspec:
            json_kspec_present.add(function)
        return json_kspec_present.data
    return None


def _generate_output_unresolved(
    kspec: Set[Tuple[str, str]], message: str, color: Callable[[str], str], generate_json: bool
) -> Optional[Dict]:
    info = ""
    for contract, function in kspec:
        info += f"{message} {contract}.{function}\n"
    if info:
        logger.info(color(info))

    if generate_json:
        json_kspec_present = output.Output(info, additional_fields={"signatures": kspec})
        return json_kspec_present.data
    return None


def _run_coverage_analysis(
    args: Namespace, slither: SlitherCompilationUnit, kspec_functions: Set[Tuple[str, str]]
) -> None:
    # Collect all slither functions
    slither_functions = _get_slither_functions(slither)

    # Determine which klab specs were not resolved.
    slither_functions_set = set(slither_functions)
    kspec_functions_resolved = kspec_functions & slither_functions_set
    kspec_functions_unresolved: Set[Tuple[str, str]] = kspec_functions - kspec_functions_resolved

    kspec_missing: List[Union[FunctionContract, StateVariable]] = []
    kspec_present: List[Union[FunctionContract, StateVariable]] = []

    for slither_func_desc in sorted(slither_functions_set):
        slither_func = slither_functions[slither_func_desc]

        if slither_func_desc in kspec_functions:
            kspec_present.append(slither_func)
        else:
            kspec_missing.append(slither_func)

    logger.info("## Check for functions coverage")
    json_kspec_present = _generate_output(kspec_present, "[✓]", green, args.json)
    json_kspec_missing_functions = _generate_output(
        [f for f in kspec_missing if isinstance(f, FunctionContract)],
        "[ ] (Missing function)",
        red,
        args.json,
    )
    json_kspec_missing_variables = _generate_output(
        [f for f in kspec_missing if isinstance(f, StateVariable)],
        "[ ] (Missing variable)",
        yellow,
        args.json,
    )
    json_kspec_unresolved = _generate_output_unresolved(
        kspec_functions_unresolved, "[ ] (Unresolved)", yellow, args.json
    )

    # Handle unresolved kspecs
    if args.json:
        output.output_to_json(
            args.json,
            None,
            {
                "functions_present": json_kspec_present,
                "functions_missing": json_kspec_missing_functions,
                "variables_missing": json_kspec_missing_variables,
                "functions_unresolved": json_kspec_unresolved,
            },
        )


def run_analysis(args: Namespace, slither: SlitherCompilationUnit, kspec_arg: str) -> None:
    # Get all of our kspec'd functions (tuple(contract_name, function_name)).
    if "," in kspec_arg:
        kspecs = kspec_arg.split(",")
        kspec_functions: Set[Tuple[str, str]] = set()
        for kspec in kspecs:
            kspec_functions |= _get_all_covered_kspec_functions(kspec)
    else:
        kspec_functions = _get_all_covered_kspec_functions(kspec_arg)

    # Run coverage analysis
    _run_coverage_analysis(args, slither, kspec_functions)
