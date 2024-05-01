#!/usr/bin/env python3

import argparse
import cProfile
import enum
import glob
import inspect
import json
import logging
import os
import pstats
import sys
import textwrap
import click
import traceback
from dataclasses import dataclass
from functools import lru_cache
from importlib import metadata
from pathlib import Path
from typing import Tuple, Optional, List, Dict, Type, Union, Any, Sequence

import typer
from typing_extensions import Annotated

from crytic_compile import cryticparser, CryticCompile
from crytic_compile.platform.standard import generate_standard_export
from crytic_compile.platform.etherscan import SUPPORTED_NETWORK
from crytic_compile import compile_all, is_supported

from slither.detectors import all_detectors
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.printers import all_printers
from slither.printers.abstract_printer import AbstractPrinter
from slither.slither import Slither
from slither.utils import codex
from slither.utils.output import (
    output_to_json,
    output_to_zip,
    output_to_sarif,
    ZIP_TYPES_ACCEPTED,
    Output,
)
from slither.utils.output_capture import StandardOutputCapture
from slither.utils.colors import red, set_colorization_enabled
from slither.utils.command_line import (
    FailOnLevel,
    output_detectors,
    output_results_to_markdown,
    output_detectors_json,
    output_printers,
    output_printers_json,
    output_to_markdown,
    output_wiki,
    defaults_flag_in_config,
    read_config_file,
    JSON_OUTPUT_TYPES,
    DEFAULT_JSON_OUTPUT_TYPES,
    check_and_sanitize_markdown_root,
    TyperDefault,
    format_crytic_help,
    read_config_file_new,
    slither_end_callback,
    SlitherState,
)
from slither.exceptions import SlitherException

logging.basicConfig()
logger = logging.getLogger("Slither")


app = TyperDefault("detect", rich_markup_mode="markdown", result_callback=slither_end_callback)

###################################################################################
###################################################################################
# region Process functions
###################################################################################
###################################################################################


def process_single(
    target: Union[str, CryticCompile],
    state: Dict,
    detector_classes: List[Type[AbstractDetector]],
    printer_classes: List[Type[AbstractPrinter]],
) -> Tuple[Slither, List[Dict], List[Output], int]:
    """
    The core high-level code for running Slither static analysis.

    Returns:
        list(result), int: Result list and number of contracts analyzed
    """
    ast = "--ast-compact-json" if not state.get("legacy_ast", False) else "--ast-json"
    slither = Slither(target, ast_format=ast, **vars(state))

    if state.get("sarif_input"):
        slither.sarif_input = state.get("sarif_input")
    if state.get("sarif_triage"):
        slither.sarif_triage = state.get("sarif_triage")

    return _process(slither, detector_classes, printer_classes)


def process_all(
    target: str,
    state: Dict,
    detector_classes: List[Type[AbstractDetector]],
    printer_classes: List[Type[AbstractPrinter]],
) -> Tuple[List[Slither], List[Dict], List[Output], int]:
    compilations = compile_all(target, **vars(state))
    slither_instances = []
    results_detectors = []
    results_printers = []
    analyzed_contracts_count = 0
    for compilation in compilations:
        (
            slither,
            current_results_detectors,
            current_results_printers,
            current_analyzed_count,
        ) = process_single(compilation, state, detector_classes, printer_classes)
        results_detectors.extend(current_results_detectors)
        results_printers.extend(current_results_printers)
        slither_instances.append(slither)
        analyzed_contracts_count += current_analyzed_count
    return (
        slither_instances,
        results_detectors,
        results_printers,
        analyzed_contracts_count,
    )


def _process(
    slither: Slither,
    detector_classes: List[Type[AbstractDetector]],
    printer_classes: List[Type[AbstractPrinter]],
) -> Tuple[Slither, List[Dict], List[Output], int]:
    for detector_cls in detector_classes:
        slither.register_detector(detector_cls)

    for printer_cls in printer_classes:
        slither.register_printer(printer_cls)

    analyzed_contracts_count = len(slither.contracts)

    results_detectors = []
    results_printers = []

    if not printer_classes:
        detector_resultss = slither.run_detectors()
        detector_resultss = [x for x in detector_resultss if x]  # remove empty results
        detector_results = [item for sublist in detector_resultss for item in sublist]  # flatten
        results_detectors.extend(detector_results)

    else:
        printer_results = slither.run_printers()
        printer_results = [x for x in printer_results if x]  # remove empty results
        results_printers.extend(printer_results)

    return slither, results_detectors, results_printers, analyzed_contracts_count


# endregion
###################################################################################
###################################################################################

# region Detectors and printers
###################################################################################
###################################################################################


@lru_cache
def get_detectors_and_printers() -> Tuple[
    List[Type[AbstractDetector]], List[Type[AbstractPrinter]]
]:
    detectors_ = [getattr(all_detectors, name) for name in dir(all_detectors)]
    detectors = [d for d in detectors_ if inspect.isclass(d) and issubclass(d, AbstractDetector)]

    printers_ = [getattr(all_printers, name) for name in dir(all_printers)]
    printers = [p for p in printers_ if inspect.isclass(p) and issubclass(p, AbstractPrinter)]

    # Handle plugins!
    if sys.version_info >= (3, 10):
        entry_points = metadata.entry_points(group="slither_analyzer.plugin")
    else:
        from pkg_resources import iter_entry_points  # pylint: disable=import-outside-toplevel

        entry_points = iter_entry_points(group="slither_analyzer.plugin", name=None)

    for entry_point in entry_points:
        make_plugin = entry_point.load()

        plugin_detectors, plugin_printers = make_plugin()

        not_detectors = {
            detector for detector in plugin_detectors if not issubclass(detector, AbstractDetector)
        }
        if not_detectors:
            raise ValueError(
                f"Error when loading plugin {entry_point}, {not_detectors} are not detectors"
            )

        not_printers = {
            printer for printer in plugin_printers if not issubclass(printer, AbstractPrinter)
        }
        if not_printers:
            raise ValueError(
                f"Error when loading plugin {entry_point}, {not_printers} are not printers"
            )

        # We convert those to lists in case someone returns a tuple
        detectors += list(plugin_detectors)
        printers += list(plugin_printers)

    return detectors, printers


# pylint: disable=too-many-branches
def choose_detectors(
    arg_detector_to_run: str,
    arg_detector_exclude: str,
    exclude_low: bool = False,
    exclude_medium: bool = False,
    exclude_high: bool = False,
    exclude_optimization: bool = False,
    exclude_informational: bool = False,
) -> List[Type[AbstractDetector]]:
    # If detectors are specified, run only these

    all_detector_classes: List[Type[AbstractDetector]] = detectors
    if all_detector_classes is None:
        return []

    detectors_to_run = []
    local_detectors = {d.ARGUMENT: d for d in all_detector_classes}

    if arg_detector_to_run == "all":
        detectors_to_run = all_detector_classes
        if arg_detector_exclude:
            detectors_excluded = arg_detector_exclude.split(",")
            for detector in local_detectors:
                if detector in detectors_excluded:
                    detectors_to_run.remove(local_detectors[detector])
    else:
        for detector in arg_detector_to_run.split(","):
            if detector in local_detectors:
                detectors_to_run.append(local_detectors[detector])
            else:
                raise ValueError(f"Error: {detector} is not a detector")
        detectors_to_run = sorted(detectors_to_run, key=lambda x: x.IMPACT)
        return detectors_to_run

    if exclude_optimization:
        detectors_to_run = [
            d for d in detectors_to_run if d.IMPACT != DetectorClassification.OPTIMIZATION
        ]

    if exclude_informational:
        detectors_to_run = [
            d for d in detectors_to_run if d.IMPACT != DetectorClassification.INFORMATIONAL
        ]
    if exclude_low:
        detectors_to_run = [d for d in detectors_to_run if d.IMPACT != DetectorClassification.LOW]
    if exclude_medium:
        detectors_to_run = [
            d for d in detectors_to_run if d.IMPACT != DetectorClassification.MEDIUM
        ]
    if exclude_high:
        detectors_to_run = [d for d in detectors_to_run if d.IMPACT != DetectorClassification.HIGH]
    if arg_detector_exclude:
        detectors_to_run = [d for d in detectors_to_run if d.ARGUMENT not in arg_detector_exclude]

    detectors_to_run = sorted(detectors_to_run, key=lambda x: x.IMPACT)

    return detectors_to_run


def choose_printers(
    args: argparse.Namespace, all_printer_classes: List[Type[AbstractPrinter]]
) -> List[Type[AbstractPrinter]]:
    printers_to_run = []

    # disable default printer
    if args.printers_to_run is None:
        return []

    if args.printers_to_run == "all":
        return all_printer_classes

    printers = {p.ARGUMENT: p for p in all_printer_classes}
    for printer in args.printers_to_run.split(","):
        if printer in printers:
            printers_to_run.append(printers[printer])
        else:
            raise ValueError(f"Error: {printer} is not a printer")
    return printers_to_run


# endregion
###################################################################################
###################################################################################
# region Command line parsing
###################################################################################
###################################################################################


def parse_filter_paths(args: argparse.Namespace, filter_path: bool) -> List[str]:
    paths = args.filter_paths if filter_path else args.include_paths
    if paths:
        return paths.split(",")
    return []


# pylint: disable=too-many-statements
def parse_args(
    detector_classes: List[Type[AbstractDetector]], printer_classes: List[Type[AbstractPrinter]]
) -> argparse.Namespace:
    usage = "slither target [flag]\n"
    usage += "\ntarget can be:\n"
    usage += "\t- file.sol // a Solidity file\n"
    usage += "\t- project_directory // a project directory. See https://github.com/crytic/crytic-compile/#crytic-compile for the supported platforms\n"
    usage += "\t- 0x.. // a contract on mainnet\n"
    usage += f"\t- NETWORK:0x.. // a contract on a different network. Supported networks: {','.join(x[:-1] for x in SUPPORTED_NETWORK)}\n"

    parser = argparse.ArgumentParser(
        description="For usage information, see https://github.com/crytic/slither/wiki/Usage",
        usage=usage,
    )

    parser.add_argument("filename", help=argparse.SUPPRESS)

    cryticparser.init(parser)

    group_misc.add_argument(
        "--json-types",
        help="Comma-separated list of result types to output to JSON, defaults to "
        + f'{",".join(output_type for output_type in DEFAULT_JSON_OUTPUT_TYPES)}. '
        + f'Available types: {",".join(output_type for output_type in JSON_OUTPUT_TYPES)}',
        action="store",
        default=defaults_flag_in_config["json-types"],
    )
    group_misc.add_argument(
        "--solc-ast",
        help="Provide the contract as a json AST",
        action="store_true",
        default=False,
    )

    codex.init_parser(parser)

    # debugger command
    parser.add_argument("--debug", help=argparse.SUPPRESS, action="store_true", default=False)

    parser.add_argument("--markdown", help=argparse.SUPPRESS, action=OutputMarkdown, default=False)

    parser.add_argument(
        "--wiki-detectors", help=argparse.SUPPRESS, action=OutputWiki, default=False
    )

    parser.add_argument(
        "--list-detectors-json",
        help=argparse.SUPPRESS,
        action=ListDetectorsJson,
        nargs=0,
        default=False,
    )

    parser.add_argument(
        "--legacy-ast",
        help=argparse.SUPPRESS,
        action="store_true",
        default=defaults_flag_in_config["legacy_ast"],
    )

    parser.add_argument(
        "--skip-assembly",
        help=argparse.SUPPRESS,
        action="store_true",
        default=defaults_flag_in_config["skip_assembly"],
    )

    parser.add_argument(
        "--perf",
        help=argparse.SUPPRESS,
        action="store_true",
        default=False,
    )

    # Disable the throw/catch on partial analyses
    parser.add_argument(
        "--disallow-partial", help=argparse.SUPPRESS, action="store_true", default=False
    )

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    args = parser.parse_args()
    read_config_file(args)

    args.filter_paths = parse_filter_paths(args, True)
    args.include_paths = parse_filter_paths(args, False)

    # Verify our json-type output is valid
    args.json_types = set(args.json_types.split(","))  # type:ignore
    for json_type in args.json_types:
        if json_type not in JSON_OUTPUT_TYPES:
            raise ValueError(f'Error: "{json_type}" is not a valid JSON result output type.')

    return args


class ListDetectors(argparse.Action):  # pylint: disable=too-few-public-methods
    def __call__(
        self, parser: Any, *args: Any, **kwargs: Any
    ) -> None:  # pylint: disable=signature-differs
        detectors, _ = get_detectors_and_printers()
        output_detectors(detectors)
        parser.exit()


class ListDetectorsJson(argparse.Action):  # pylint: disable=too-few-public-methods
    def __call__(
        self, parser: Any, *args: Any, **kwargs: Any
    ) -> None:  # pylint: disable=signature-differs
        detectors, _ = get_detectors_and_printers()
        detector_types_json = output_detectors_json(detectors)
        print(json.dumps(detector_types_json))
        parser.exit()


def list_detectors_json(value: bool):
    if not value:
        return

    detector_types_json = output_detectors_json(detectors)
    print(json.dumps(detector_types_json))
    raise typer.Exit(code=0)


def list_detectors_action(value: bool) -> None:
    if not value:
        return

    output_detectors(detectors)
    raise typer.Exit()


def list_printers_action(value: bool) -> None:
    if not value:
        return

    output_printers(printers)
    raise typer.Exit()


class ListPrinters(argparse.Action):  # pylint: disable=too-few-public-methods
    def __call__(
        self, parser: Any, *args: Any, **kwargs: Any
    ) -> None:  # pylint: disable=signature-differs
        _, printers = get_detectors_and_printers()
        output_printers(printers)
        parser.exit()


class OutputMarkdown(argparse.Action):  # pylint: disable=too-few-public-methods
    def __call__(
        self,
        parser: Any,
        args: Any,
        values: Optional[Union[str, Sequence[Any]]],
        option_string: Any = None,
    ) -> None:
        detectors, printers = get_detectors_and_printers()
        assert isinstance(values, str)
        output_to_markdown(detectors, printers, values)
        parser.exit()


class OutputWiki(argparse.Action):  # pylint: disable=too-few-public-methods
    def __call__(
        self,
        parser: Any,
        args: Any,
        values: Optional[Union[str, Sequence[Any]]],
        option_string: Any = None,
    ) -> None:
        detectors, _ = get_detectors_and_printers()
        assert isinstance(values, str)
        output_wiki(detectors, values)
        parser.exit()


# endregion
###################################################################################
###################################################################################
# region CustomFormatter
###################################################################################
###################################################################################


class FormatterCryticCompile(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        # for i, msg in enumerate(record.msg):
        if record.msg.startswith("Compilation warnings/errors on "):
            txt = record.args[1]  # type:ignore
            txt = txt.split("\n")  # type:ignore
            txt = [red(x) if "Error" in x else x for x in txt]
            txt = "\n".join(txt)
            record.args = (record.args[0], txt)  # type:ignore
        return super().format(record)


# endregion
###################################################################################
###################################################################################
# region Main
###################################################################################
###################################################################################


# pylint: disable=too-many-statements,too-many-branches,too-many-locals
def main_impl(
    all_detector_classes: List[Type[AbstractDetector]],
    all_printer_classes: List[Type[AbstractPrinter]],
) -> None:
    """
    :param all_detector_classes: A list of all detectors that can be included/excluded.
    :param all_printer_classes: A list of all printers that can be included.
    """
    # Set logger of Slither to info, to catch warnings related to the arg parsing
    logger.setLevel(logging.INFO)
    args = parse_args(all_detector_classes, all_printer_classes)

    cp: Optional[cProfile.Profile] = None
    if args.perf:
        cp = cProfile.Profile()
        cp.enable()

    # Set colorization option
    set_colorization_enabled(False if args.disable_color else sys.stdout.isatty())

    # Define some variables for potential JSON output
    json_results: Dict[str, Any] = {}
    output_error = None
    outputting_json = args.json is not None
    outputting_json_stdout = args.json == "-"
    outputting_sarif = args.sarif is not None
    outputting_sarif_stdout = args.sarif == "-"
    outputting_zip = args.zip is not None
    if args.zip_type not in ZIP_TYPES_ACCEPTED:
        to_log = f'Zip type not accepted, it must be one of {",".join(ZIP_TYPES_ACCEPTED.keys())}'
        logger.error(to_log)

    # If we are outputting JSON, capture all standard output. If we are outputting to stdout, we block typical stdout
    # output.
    if outputting_json or outputting_sarif:
        StandardOutputCapture.enable(outputting_json_stdout or outputting_sarif_stdout)

    printer_classes = choose_printers(args, all_printer_classes)
    detector_classes = choose_detectors(args, all_detector_classes)

    results_detectors: List[Dict] = []
    results_printers: List[Output] = []
    try:
        filename = args.filename

        # Determine if we are handling ast from solc
        if args.solc_ast or (filename.endswith(".json") and not is_supported(filename)):
            globbed_filenames = glob.glob(filename, recursive=True)
            filenames = glob.glob(os.path.join(filename, "*.json"))
            if not filenames:
                filenames = globbed_filenames
            number_contracts = 0

            slither_instances = []
            for filename in filenames:
                (
                    slither_instance,
                    results_detectors_tmp,
                    results_printers_tmp,
                    number_contracts_tmp,
                ) = process_single(filename, args, detector_classes, printer_classes)
                number_contracts += number_contracts_tmp
                results_detectors += results_detectors_tmp
                results_printers += results_printers_tmp
                slither_instances.append(slither_instance)

        # Rely on CryticCompile to discern the underlying type of compilations.
        else:
            (
                slither_instances,
                results_detectors,
                results_printers,
                number_contracts,
            ) = process_all(filename, args, detector_classes, printer_classes)

        # Determine if we are outputting JSON
        if outputting_json or outputting_zip or output_to_sarif:
            # Add our compilation information to JSON
            if "compilations" in args.json_types:
                compilation_results = []
                for slither_instance in slither_instances:
                    assert slither_instance.crytic_compile
                    compilation_results.append(
                        generate_standard_export(slither_instance.crytic_compile)
                    )
                json_results["compilations"] = compilation_results

            # Add our detector results to JSON if desired.
            if results_detectors and "detectors" in args.json_types:
                json_results["detectors"] = results_detectors

            # Add our printer results to JSON if desired.
            if results_printers and "printers" in args.json_types:
                json_results["printers"] = results_printers

            # Add our detector types to JSON
            if "list-detectors" in args.json_types:
                detectors, _ = get_detectors_and_printers()
                json_results["list-detectors"] = output_detectors_json(detectors)

            # Add our detector types to JSON
            if "list-printers" in args.json_types:
                _, printers = get_detectors_and_printers()
                json_results["list-printers"] = output_printers_json(printers)

        # Output our results to markdown if we wish to compile a checklist.
        if args.checklist:
            output_results_to_markdown(
                results_detectors, args.checklist_limit, args.show_ignored_findings
            )

        # Don't print the number of result for printers
        if number_contracts == 0:
            logger.warning(red("No contract was analyzed"))
        if printer_classes:
            logger.info("%s analyzed (%d contracts)", filename, number_contracts)
        else:
            logger.info(
                "%s analyzed (%d contracts with %d detectors), %d result(s) found",
                filename,
                number_contracts,
                len(detector_classes),
                len(results_detectors),
            )

    except SlitherException as slither_exception:
        output_error = str(slither_exception)
        traceback.print_exc()
        logging.error(red("Error:"))
        logging.error(red(output_error))
        logging.error("Please report an issue to https://github.com/crytic/slither/issues")

    # If we are outputting JSON, capture the redirected output and disable the redirect to output the final JSON.
    if outputting_json:
        if "console" in args.json_types:
            json_results["console"] = {
                "stdout": StandardOutputCapture.get_stdout_output(),
                "stderr": StandardOutputCapture.get_stderr_output(),
            }
        StandardOutputCapture.disable()
        output_to_json(None if outputting_json_stdout else args.json, output_error, json_results)

    if outputting_sarif:
        StandardOutputCapture.disable()
        output_to_sarif(
            None if outputting_sarif_stdout else args.sarif, json_results, detector_classes
        )

    if outputting_zip:
        output_to_zip(args.zip, output_error, json_results, args.zip_type)

    if args.perf and cp:
        cp.disable()
        stats = pstats.Stats(cp).sort_stats("cumtime")
        stats.print_stats()

    fail_on = FailOnLevel(args.fail_on)
    if fail_on == FailOnLevel.HIGH:
        fail_on_detection = any(result["impact"] == "High" for result in results_detectors)
    elif fail_on == FailOnLevel.MEDIUM:
        fail_on_detection = any(
            result["impact"] in ["Medium", "High"] for result in results_detectors
        )
    elif fail_on == FailOnLevel.LOW:
        fail_on_detection = any(
            result["impact"] in ["Low", "Medium", "High"] for result in results_detectors
        )
    elif fail_on == FailOnLevel.PEDANTIC:
        fail_on_detection = bool(results_detectors)
    else:
        fail_on_detection = False

    # Exit with them appropriate status code
    if output_error or fail_on_detection:
        sys.exit(-1)
    else:
        sys.exit(0)


@dataclass
class Target:
    target: Union[str, Path]

    HELP: str = textwrap.dedent(
        f"""
    Target can be:

    - *file.sol*: a Solidity file
    
    - *project_directory*: a project directory. 
      See the [documentation](https://github.com/crytic/crytic-compile/#crytic-compile) for the supported 
      platforms.
    
    - *0x..* : a contract address on mainnet
    
    - *NETWORK:0x..*: a contract on a different network.
      Supported networks: {', '.join(x[:-1] for x in SUPPORTED_NETWORK)}
    """
    )

    def __str__(self) -> str:
        return "XXX"


class TargetParam(click.ParamType):
    name = "Target"

    def convert(self, value: Union[str, Path], param, ctx):
        return Target(value)


target_type = Annotated[
    Optional[Target], typer.Argument(..., help=Target.HELP, click_type=TargetParam())
]


def version_callback(value: bool) -> None:
    if not value:
        return

    print(metadata.version("slither-analyzer"))
    raise typer.Exit(code=0)


detectors, printers = get_detectors_and_printers()


class OutputFormat(str, enum.Enum):
    TEXT = "text"
    JSON = "json"
    SARIF = "sarif"
    ZIP = "zip"


class PathList(click.ParamType):
    name = "PathList"

    def convert(self, value: Union[str, None], param, ctx) -> List[str]:
        if value is None:
            return []

        paths = value.split(",")
        return paths


class MarkdownRoot(click.ParamType):
    name = "MarkdownRoot"

    def convert(self, value: str, param, ctx) -> str:
        return check_and_sanitize_markdown_root(value)


def parse_extra_arguments(args: List[str]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    if not args:
        return {}, {}

    parser = argparse.ArgumentParser(allow_abbrev=False)
    cryticparser.init(parser)

    parsed_args, remaining_args = parser.parse_known_args(args)

    return parsed_args, remaining_args


def long_help(ctx: typer.Context, _, value) -> None:
    if value is True:
        format_crytic_help(ctx)
        ctx.get_help()
        raise typer.Exit()


@app.command(
    context_settings={"ignore_unknown_options": True, "allow_extra_args": True},
)
def detect(
    ctx: typer.Context,
    target: target_type,
    help_long: Annotated[
        bool,
        typer.Option(
            "--help-long",
            help="Help for crytic compile options.",
            is_eager=True,
            callback=long_help,
        ),
    ] = False,
    list_json_detector: Annotated[
        Optional[bool],
        typer.Option("--list-detectors-json", callback=list_detectors_json, hidden=True),
    ] = None,
    list_detectors: Annotated[
        Optional[bool],
        typer.Option(
            "--list-detectors",
            help="List available detectors.",
            callback=list_detectors_action,
            rich_help_panel="Detectors",
        ),
    ] = None,
    detectors_to_run: Annotated[
        Optional[str],
        typer.Option(
            "--detect",
            help=f"Comma-separated list of detectors. Available detectors: {', '.join(d.ARGUMENT for d in detectors)}",
            rich_help_panel="Detectors",
        ),
    ] = defaults_flag_in_config["detectors_to_run"],
    detectors_to_exclude: Annotated[
        Optional[str],
        typer.Option(
            "--exclude",
            help="Comma-separated list of detectors that should be excluded.",
            rich_help_panel="Detectors",
        ),
    ] = defaults_flag_in_config["detectors_to_exclude"],
    exclude_dependencies: Annotated[
        Optional[bool],
        typer.Option(
            "--exclude-dependencies",
            help="Exclude results that are only related to dependencies.",
            rich_help_panel="Detectors",
        ),
    ] = defaults_flag_in_config["exclude_dependencies"],
    exclude_optimization: Annotated[
        Optional[bool],
        typer.Option(
            "--exclude-optimization",
            help="Exclude optimization analyses.",
            rich_help_panel="Detectors",
        ),
    ] = defaults_flag_in_config["exclude_optimization"],
    exclude_informational: Annotated[
        Optional[bool],
        typer.Option(
            "--exclude-informational",
            help="Exclude informational impact analyses.",
            rich_help_panel="Detectors",
        ),
    ] = defaults_flag_in_config["exclude_informational"],
    exclude_low: Annotated[
        Optional[bool],
        typer.Option(
            "--exclude-low",
            help="Exclude low impact analyses.",
            rich_help_panel="Detectors",
        ),
    ] = defaults_flag_in_config["exclude_low"],
    exclude_medium: Annotated[
        Optional[bool],
        typer.Option(
            "--exclude-medium",
            help="Exclude medium impact analyses.",
            rich_help_panel="Detectors",
        ),
    ] = defaults_flag_in_config["exclude_medium"],
    exclude_high: Annotated[
        Optional[bool],
        typer.Option(
            "--exclude-high",
            help="Exclude high impact analyses.",
            rich_help_panel="Detectors",
        ),
    ] = defaults_flag_in_config["exclude_high"],
    show_ignored_findings: Annotated[
        Optional[bool],
        typer.Option(
            "--show-ignored-findings",
            help="Show all the findings.",
            rich_help_panel="Detectors",
        ),
    ] = defaults_flag_in_config["show_ignored_findings"],
    checklist: Annotated[
        Optional[bool],
        typer.Option(
            "--checklist",
            help="Generate a markdown page with the detector results.",
            rich_help_panel="Detectors",
        ),
    ] = False,
    checklist_limit: Annotated[
        Optional[int],
        typer.Option(
            "--checklist-limit",
            help="Limit the number of results per detector in the markdown file.",
            rich_help_panel="Detectors",
        ),
    ] = 0,
    markdown_root: Annotated[
        Optional[str],
        typer.Option(
            "--markdown-root",
            help="URL for markdown generation.",
            rich_help_panel="Detectors",
            click_type=MarkdownRoot(),
        ),
    ] = "",
    sarif_input: Annotated[
        Path,
        typer.Option(
            "--sarif-input",
            help="Sarif input (beta).",
            rich_help_panel="Detectors",
        ),
    ] = defaults_flag_in_config["sarif_input"],
    sarif_triage: Annotated[
        Path,
        typer.Option(
            "--sarif-triage",
            help="Sarif triage (beta).",
            rich_help_panel="Detectors",
        ),
    ] = defaults_flag_in_config["sarif_triage"],
    triage_mode: Annotated[
        bool,
        typer.Option(
            "--triage-mode",
            help=f"Run triage mode (save results in triage database).",
            rich_help_panel="Detectors",
        ),
    ] = False,
    triage_database: Annotated[
        Path,
        typer.Option(
            "--triage-database",
            help="File path to the triage database (default: slither.db.json)",
            rich_help_panel="Detectors",
        ),
    ] = defaults_flag_in_config["triage_database"],
    change_line_prefix: Annotated[
        str,
        typer.Option(
            "--change-line-prefix",
            help="Change the line prefix (default #) for the displayed source codes (i.e. file.sol#1).",
            rich_help_panel="Detectors",
        ),
    ] = "#",  # TODO(dm) change me to ":"
    solc_ast: bool = False,  # Unused,
    json_types: Optional[str] = None,  # Unused
    generate_patches: Annotated[
        bool,
        typer.Option(
            "--generate-patches",
            help="Generate patches (json output only).",
            rich_help_panel="Detectors",
        ),
    ] = False,
    fail_pedantic: Annotated[
        bool,
        typer.Option(
            "--fail-pedantic",
            help="Fail if any findings are detected.",
            rich_help_panel="Reporting mode",
            hidden=True,
        ),
    ] = False,
    fail_low: Annotated[
        bool,
        typer.Option(
            "--fail-low",
            help="Fail if any low or greater impact findings are detected.",
            rich_help_panel="Reporting mode",
            hidden=True,
        ),
    ] = False,
    fail_medium: Annotated[
        bool,
        typer.Option(
            "--fail-medium",
            help="Fail if any medium or greater impact findings are detected.",
            rich_help_panel="Reporting mode",
            hidden=True,
        ),
    ] = False,
    fail_high: Annotated[
        bool,
        typer.Option(
            "--fail-high",
            help="Fail if any high or greater impact findings are detected.",
            rich_help_panel="Reporting mode",
            hidden=True,
        ),
    ] = False,
    fail_none: Annotated[
        bool,
        typer.Option(
            "--fail-none",
            "--no-fail-pedantic",
            help="Do not return the number of findings in the exit code.",
            rich_help_panel="Reporting mode",
            hidden=True,
        ),
    ] = False,
    fail_on: Annotated[
        FailOnLevel,
        typer.Option(
            "--fail-on",
            help=textwrap.dedent(
                f"""
                Fail level:
                - *pedantic* : Fail if any findings are detected.

                - *none*: Do not return the number of findings in the exit code.

                - *low*: Fail if any low or greater impact findings are detected.

                - *medium*: Fail if any medium or greater impact findings are detected.

                - *high*: Fail if any high or greater impact findings are detected.
                """
            ),
            rich_help_panel="Reporting mode",
        ),
    ] = FailOnLevel.PEDANTIC.value,
    # Filtering
    filter_paths: Annotated[
        Optional[List[str]],
        typer.Option(
            help="Regex filter to exclude detector results matching file path e.g. (mocks/|test/).",
            click_type=PathList(),
            rich_help_panel="Filtering",
        ),
    ] = defaults_flag_in_config["filter_paths"],
    include_paths: Annotated[
        Optional[List[str]],
        typer.Option(
            help="Regex filter to include detector results matching file path e.g. (src/|contracts/).",
            click_type=PathList(),
            rich_help_panel="Filtering",
        ),
    ] = defaults_flag_in_config["include_paths"],
):

    crytic_args = {}
    if ctx.args:
        crytic_args, remaining_args = parse_extra_arguments(ctx.args)

        if remaining_args:
            raise typer.BadParameter(f"Found additional parameters. {remaining_args}")

    detector_classes = choose_detectors(
        detectors_to_run,
        detectors_to_exclude,
        exclude_low,
        exclude_medium,
        exclude_high,
        exclude_optimization,
        exclude_informational,
    )

    if fail_on == FailOnLevel.PEDANTIC:
        fail_levels = {level: locals().get(f"fail_{level.value}") for level in FailOnLevel}
        count = list(fail_levels.values()).count(True)
        if count == 1:
            print("Deprecated way of setting levels.")
            fail_on = FailOnLevel([level for level in fail_levels if fail_levels[level]].pop())
        elif count > 1:
            raise typer.BadParameter("Only one fail level is allowed.")
        else:
            fail_on = FailOnLevel.PEDANTIC

    slither_instances, results_detectors, _, output_errors, number_contracts = handle_target(
        ctx,
        target,
        solc_ast=solc_ast,
        detectors_to_run=detector_classes,
        crytic_args=crytic_args,
    )

    if number_contracts == 0:
        logger.warning(red("No contract was analyzed"))
    else:
        logger.info(
            "%s analyzed (%d contracts with %d detectors), %d result(s) found",
            target.target,
            number_contracts,
            len(detector_classes),
            len(results_detectors),
        )

    state = ctx.ensure_object(SlitherState)

    format_output(
        state,
        state.get("output_format"),
        state.get("output_file"),
        slither_instances,
        results_detectors,
        [],
        output_errors,
        runned_detectors=detector_classes,
        runned_printers=[],
    )

    if fail_on == FailOnLevel.HIGH:
        fail_on_detection = any(result["impact"] == "High" for result in results_detectors)
    elif fail_on == FailOnLevel.MEDIUM:
        fail_on_detection = any(
            result["impact"] in ["Medium", "High"] for result in results_detectors
        )
    elif fail_on == FailOnLevel.LOW:
        fail_on_detection = any(
            result["impact"] in ["Low", "Medium", "High"] for result in results_detectors
        )
    elif fail_on == FailOnLevel.PEDANTIC:
        fail_on_detection = bool(results_detectors)
    else:
        fail_on_detection = False

    # Exit with them appropriate status code
    if output_errors or fail_on_detection:
        raise typer.Exit(1)


@app.command(name="print")
def printer_command(
    ctx: typer.Context,
    target: target_type,
    list_printers: Annotated[
        Optional[bool],
        typer.Option(
            "--list-detectors",
            help="List available printers.",
            callback=list_printers_action,
            rich_help_panel="Printers",
        ),
    ] = None,
    printers_to_run: Annotated[
        Optional[str],
        typer.Option(
            "--print",
            help="Comma-separated list of contract information printers, "
            f"available printers: {', '.join(d.ARGUMENT for d in printers)}",
            rich_help_panel="Printers",
        ),
    ] = defaults_flag_in_config["printers_to_run"],
):
    pass


def handle_target(
    ctx: typer.Context,
    target: Target,
    solc_ast: bool = False,
    detectors_to_run: Optional[List[Type[AbstractDetector]]] = None,
    printers_to_run: Optional[List[Type[AbstractPrinter]]] = None,
    crytic_args: Union[Dict[str, str], None] = None,
):

    if detectors_to_run is None:
        detectors_to_run = []

    if printers_to_run is None:
        printers_to_run = []

    if crytic_args is None:
        crytic_args = {}

    state = ctx.ensure_object(SlitherState)
    state.update(crytic_args)

    results_detectors: List[Dict] = []
    results_printers: List[Output] = []
    output_error: Union[str, None] = None
    slither_instances = []

    try:
        filename = target.target

        if solc_ast or (filename.endswith(".json") and not is_supported(filename)):
            globbed_filenames = glob.glob(filename, recursive=True)

            filenames = glob.glob(os.path.join(filename, "*.json"))
            if not filenames:
                filenames = globbed_filenames
            number_contracts = 0

            for filename in filenames:
                (
                    slither_instance,
                    results_detectors_tmp,
                    results_printers_tmp,
                    number_contracts_tmp,
                ) = process_single(filename, state, detectors_to_run, printers_to_run)
                number_contracts += number_contracts_tmp
                results_detectors += results_detectors_tmp
                results_printers += results_printers_tmp
                slither_instances.append(slither_instance)

        # Rely on CryticCompile to discern the underlying type of compilations.
        else:
            (
                slither_instances,
                results_detectors,
                results_printers,
                number_contracts,
            ) = process_all(filename, state, detectors_to_run, printers_to_run)

    except SlitherException as slither_exception:
        output_error = str(slither_exception)
        traceback.print_exc()
        logging.error(red("Error:"))
        logging.error(red(output_error))
        logging.error("Please report an issue to https://github.com/crytic/slither/issues")

    return slither_instances, results_detectors, results_printers, output_error, number_contracts


def format_output(
    state: Dict[str, Any],
    output_format: OutputFormat,
    output_file: Path,
    slither_instances,
    results_detectors,
    results_printers,
    output_error,
    runned_detectors: Union[List[Type[AbstractDetector]], None] = None,
    runned_printers: Union[List[Type[AbstractPrinter]], None] = None,
):
    if output_format in (OutputFormat.JSON, OutputFormat.SARIF, OutputFormat.ZIP):
        json_results: Dict[str, Any] = {}

        json_types = state.get("json_types", [])
        if "compilation" in json_types:
            compilation_results = []
            for slither_instance in slither_instances:
                assert slither_instance.crytic_compile
                compilation_results.append(
                    generate_standard_export(slither_instance.crytic_compile)
                )
            json_results["compilations"] = compilation_results

        # Add our detector results to JSON if desired.
        if results_detectors and "detectors" in json_types:
            json_results["detectors"] = results_detectors

        # Add our printer results to JSON if desired.
        if results_printers and "printers" in json_types:
            json_results["printers"] = results_printers

        # Add our detector types to JSON
        if "list-detectors" in json_types:
            json_results["list-detectors"] = output_detectors_json(detectors)

        # Add our detector types to JSON
        if "list-printers" in json_types:
            json_results["list-printers"] = output_printers_json(printers)

        if output_format == OutputFormat.JSON:
            if "console" in json_types:
                json_results["console"] = {
                    "stdout": StandardOutputCapture.get_stdout_output(),
                    "stderr": StandardOutputCapture.get_stderr_output(),
                }
            StandardOutputCapture.disable()
            output_to_json(output_file.as_posix(), output_error, json_results)
        elif output_format == OutputFormat.SARIF:
            StandardOutputCapture.disable()
            output_to_sarif(output_file.as_posix(), json_results, runned_detectors)
        elif output_format == OutputFormat.ZIP:
            output_to_zip(output_file.as_posix(), output_error, json_results, state.get("zip_type"))

    elif state.get("checklist", False) is True:
        output_results_to_markdown(
            results_detectors,
            state.get("checklist_limit", defaults_flag_in_config["checklist_limit"]),
            state.get("show_ignored_findings", defaults_flag_in_config["show_ignored_findings"]),
        )


@app.callback(invoke_without_command=True)
def callback(
    ctx: typer.Context,
    version: Annotated[
        Optional[bool],
        typer.Option(
            "--version",
            callback=version_callback,
            help="Displays the current version.",
            is_eager=True,
        ),
    ] = None,
    output_format: Annotated[
        OutputFormat,
        typer.Option("--output-format", help="Output format.", rich_help_panel="Formatting"),
    ] = OutputFormat.TEXT,
    output_file: Annotated[
        Path, typer.Option("--output-file", help="Output file. Use - for stdout.")
    ] = "-",
    zip_: Annotated[
        bool,
        typer.Option(
            "--zip",
            help="Export the results as a zipped JSON file.",
            rich_help_panel="Detectors",
        ),
    ] = defaults_flag_in_config["zip"],
    zip_type: Annotated[
        Optional[str],
        typer.Option(
            "--zip-type",
            help=f'Zip compression type. One of {",".join(ZIP_TYPES_ACCEPTED.keys())}. Default lzma',
            rich_help_panel="Detectors",
        ),
    ] = defaults_flag_in_config["zip_type"],
    disable_color: Annotated[
        bool,
        typer.Option(
            "--disable-color",
            help=f"Disable output colorization. "
            f"Implicit if the output format is not {OutputFormat.TEXT.value}.",
            rich_help_panel="Formatting",
        ),
    ] = defaults_flag_in_config["disable_color"],
    # Misc
    no_fail: Annotated[
        bool,
        typer.Option(
            "--no-fail",
            help="Do not fail in case of parsing (echidna mode only).",
            rich_help_panel="Misc",
        ),
    ] = defaults_flag_in_config["no_fail"],
    config_file: Annotated[
        Optional[Path],
        typer.Option(
            "--config-file",
            help="Provide a config file (default: slither.config.json).",
            rich_help_panel="Misc",
        ),
    ] = None,
    debug: Annotated[bool, typer.Option(hidden=True)] = False,
    markdown: Annotated[bool, typer.Option(hidden=True)] = False,
    wiki_detectors: bool = False,  # TODO(dm)
    legacy_ast: Annotated[bool, typer.Option(hidden=True)] = False,
    skip_assembly: Annotated[bool, typer.Option(hidden=True)] = False,
    perf: Annotated[bool, typer.Option(hidden=True)] = False,
    disallow_partial: Annotated[bool, typer.Option(hidden=True)] = False,
):
    """Main callback"""
    state = ctx.ensure_object(SlitherState)

    if perf:
        state["perf"] = cProfile.Profile()
        state["perf"].enable()

    # Formatting configuration
    if output_format != OutputFormat.TEXT:
        disable_color = True

    set_colorization_enabled(False if disable_color else sys.stdout.isatty())

    if output_format in (OutputFormat.JSON, OutputFormat.SARIF):
        StandardOutputCapture.enable(output_file == Path("-"))

    config = read_config_file_new(config_file)

    log_level = logging.INFO if not debug else logging.DEBUG
    configure_logger(log_level)

    # Update the state with the current
    locals_vars = locals()
    for option in config:
        if option in locals_vars:
            state[option] = locals_vars[option]
        else:
            state[option] = config[option]

    if zip_ != defaults_flag_in_config["zip"]:
        output_format = OutputFormat.ZIP

    state["output_format"] = output_format
    state["output_file"] = output_file


def configure_logger(log_level):
    for logger_name in [
        "Slither",
        "Contract",
        "Function",
        "Node",
        "Parsing",
        "Detectors",
        "FunctionSolc",
        "ExpressionParsing",
        "TypeParsing",
        "SSA_Conversion",
        "Printers",
    ]:

        current_logger = logging.getLogger(logger_name)
        current_logger.setLevel(log_level)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    console_handler.setFormatter(FormatterCryticCompile())

    crytic_compile_error = logging.getLogger("CryticCompile")
    crytic_compile_error.addHandler(console_handler)
    crytic_compile_error.propagate = False
    crytic_compile_error.setLevel(logging.INFO)


if __name__ == "__main__":
    logger.setLevel(logging.INFO)

    # Codebase with complex dominators can lead to a lot of SSA recursive call
    sys.setrecursionlimit(1500)

    app()

# endregion
