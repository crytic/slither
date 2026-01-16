#!/usr/bin/env python3
import cProfile
import glob
import inspect
import json
import logging
import os
import sys
import textwrap
import traceback
from functools import lru_cache
from importlib import metadata
from pathlib import Path
from typing import Tuple, Optional, List, Dict, Type, Union, Any
import warnings

# pylint: disable=wrong-import-position
# We want to disable the warnings thrown by any package when using the completion
if os.environ.get("_TYPER_COMPLETE_ARGS", False):
    warnings.filterwarnings("ignore")

# Configure logging BEFORE importing crytic_compile to suppress INFO messages
logging.basicConfig()
logging.getLogger("CryticCompile").setLevel(logging.WARNING)

import typer  # noqa: E402
from typing_extensions import Annotated  # noqa: E402

from crytic_compile import CryticCompile, InvalidCompilation  # noqa: E402
from crytic_compile import compile_all, is_supported  # noqa: E402

from slither.detectors import all_detectors  # noqa: E402
from slither.detectors.abstract_detector import AbstractDetector  # noqa: E402
from slither.detectors.classification import DetectorClassification  # noqa: E402
from slither.printers import all_printers  # noqa: E402
from slither.printers.abstract_printer import AbstractPrinter  # noqa: E402
from slither.slither import Slither  # noqa: E402
from slither.utils.output import (  # noqa: E402
    Output,
    ZipType,
    OutputFormat,
    format_output,
    output_to_markdown,
    output_wiki,
    output_detectors,
    output_detectors_json,
    output_printers,
)
from slither.utils.output_capture import StandardOutputCapture  # noqa: E402
from slither.utils.colors import red, set_colorization_enabled  # noqa: E402
from slither.utils.command_line import (  # noqa: E402
    FailOnLevel,
    defaults_flag_in_config,
    DEFAULT_JSON_OUTPUT_TYPES,
    SlitherApp,
    slither_end_callback,
    SlitherState,
    version_callback,
    MarkdownRoot,
    CommaSeparatedValueParser,
    long_help,
    Target,
    target_type,
    read_config_file,
)
from slither.exceptions import SlitherException  # noqa: E402

logger = logging.getLogger("Slither")

app = SlitherApp("detect", rich_markup_mode="markdown", result_callback=slither_end_callback)

# Because the app will be used by the tools to add commands, we need to define it before importing them
import slither.tools  # noqa: E402  # pylint: disable=unused-import,wrong-import-position

###################################################################################
###################################################################################
# region Process functions
###################################################################################
###################################################################################


def process_single(
    target: Union[str, CryticCompile],
    state: Dict[str, Any],
    detector_classes: List[Type[AbstractDetector]],
    printer_classes: List[Type[AbstractPrinter]],
) -> Tuple[Slither, List[Dict], List[Output], int]:
    """
    The core high-level code for running Slither static analysis.

    Returns:
        list(result), int: Result list and number of contracts analyzed
    """
    ast = "--ast-compact-json" if not state.get("legacy_ast", False) else "--ast-json"
    slither_ = Slither(target, ast_format=ast, **state)

    if state.get("sarif_input"):
        slither_.sarif_input = state.get("sarif_input")
    if state.get("sarif_triage"):
        slither_.sarif_triage = state.get("sarif_triage")

    return _process(slither_, detector_classes, printer_classes)


def process_all(
    target: str,
    state: Dict,
    detector_classes: List[Type[AbstractDetector]],
    printer_classes: List[Type[AbstractPrinter]],
) -> Tuple[List[Slither], List[Dict], List[Output], int]:
    try:
        compilations = compile_all(target, **state)
    except InvalidCompilation:
        logger.error("Unable to compile all targets.")
        raise typer.Exit(code=2)

    slither_instances = []
    results_detectors = []
    results_printers = []
    analyzed_contracts_count = 0
    for compilation in compilations:
        (
            slither_,
            current_results_detectors,
            current_results_printers,
            current_analyzed_count,
        ) = process_single(compilation, state, detector_classes, printer_classes)
        results_detectors.extend(current_results_detectors)
        results_printers.extend(current_results_printers)
        slither_instances.append(slither_)
        analyzed_contracts_count += current_analyzed_count
    return (
        slither_instances,
        results_detectors,
        results_printers,
        analyzed_contracts_count,
    )


def _process(
    slither_: Slither,
    detector_classes: List[Type[AbstractDetector]],
    printer_classes: List[Type[AbstractPrinter]],
) -> Tuple[Slither, List[Dict], List[Output], int]:
    for detector_cls in detector_classes:
        slither_.register_detector(detector_cls)

    for printer_cls in printer_classes:
        slither_.register_printer(printer_cls)

    analyzed_contracts_count = len(slither_.contracts)

    results_detectors = []
    results_printers = []

    if not printer_classes:
        detector_resultss = slither_.run_detectors()
        detector_resultss = [x for x in detector_resultss if x]  # remove empty results
        detector_results = [item for sublist in detector_resultss for item in sublist]  # flatten
        results_detectors.extend(detector_results)

    else:
        printer_results = slither_.run_printers()
        printer_results = [x for x in printer_results if x]  # remove empty results
        results_printers.extend(printer_results)

    return slither_, results_detectors, results_printers, analyzed_contracts_count


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
        # Use importlib_metadata backport for Python < 3.10
        import importlib_metadata  # pylint: disable=import-outside-toplevel

        entry_points = importlib_metadata.entry_points(group="slither_analyzer.plugin")

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


# pylint: disable=too-many-branches,too-many-arguments
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

    all_detector_classes: List[Type[AbstractDetector]] = DETECTORS
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
    arg_printer_to_run: Union[None, str] = None,
) -> List[Type[AbstractPrinter]]:
    printers_to_run = []

    # disable default printer
    if arg_printer_to_run is None:
        return []

    if arg_printer_to_run == "all":
        return PRINTERS

    printers = {p.ARGUMENT: p for p in PRINTERS}
    for printer in arg_printer_to_run.split(","):
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


def list_detectors_json(ctx: typer.Context, value: bool):
    if not value or ctx.resilient_parsing:
        return

    detector_types_json = output_detectors_json(DETECTORS)
    print(json.dumps(detector_types_json))
    raise typer.Exit(code=0)


def list_detectors_action(ctx: typer.Context, value: bool) -> None:
    if not value or ctx.resilient_parsing:
        return

    state = ctx.ensure_object(SlitherState)
    output_format: OutputFormat = state.get("output_format", OutputFormat.TEXT)
    if output_format == OutputFormat.JSON:
        StandardOutputCapture.disable()
        list_detectors_json(ctx, True)

    if output_format != OutputFormat.TEXT:
        StandardOutputCapture.disable()
        logger.error("Unable to output detectors in another format than TEXT or JSON.")
        raise typer.Exit(code=1)

    output_detectors(DETECTORS)
    raise typer.Exit()


def list_printers_action(ctx: typer.Context, value: bool) -> None:
    if not value or ctx.resilient_parsing:
        return

    output_printers(PRINTERS)
    raise typer.Exit()


def output_markdown_action(ctx: typer.Context, value: Union[str, None]) -> None:
    if value is None or ctx.resilient_parsing:
        return

    output_to_markdown(DETECTORS, PRINTERS, value)
    raise typer.Exit()


def output_wiki_action(ctx: typer.Context, _: str, value: Union[str, None] = None):
    if ctx.resilient_parsing or value is None:
        return

    output_wiki(DETECTORS, value)
    raise typer.Exit()


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


# Find all detectors and printers
DETECTORS, PRINTERS = get_detectors_and_printers()


def complete_detectors(incomplete: str) -> List[str]:
    """Autocomplete for detector names."""
    return [d.ARGUMENT for d in DETECTORS if d.ARGUMENT.startswith(incomplete)]


def complete_printers(incomplete: str) -> List[str]:
    """Autocomplete for printer names."""
    return [p.ARGUMENT for p in PRINTERS if p.ARGUMENT.startswith(incomplete)]


# pylint: disable=unused-argument,too-many-locals
@app.command(
    help="Run slither detectors on the target.",
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
            is_eager=True,
        ),
    ] = None,
    detectors_to_run: Annotated[
        Optional[str],
        typer.Option(
            "--detect",
            help=f"Comma-separated list of detectors. Available detectors: {', '.join(d.ARGUMENT for d in DETECTORS)}",
            rich_help_panel="Detectors",
            autocompletion=complete_detectors,
        ),
    ] = defaults_flag_in_config["detectors_to_run"],
    detectors_to_exclude: Annotated[
        Optional[str],
        typer.Option(
            "--exclude",
            help="Comma-separated list of detectors that should be excluded or all.",
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
    ] = None,
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
            help="Run triage mode (save results in triage database).",
            rich_help_panel="Detectors",
        ),
    ] = False,
    triage_database: Annotated[
        Path,
        typer.Option(
            "--triage-database",
            help="File path to the triage database.",
            rich_help_panel="Detectors",
        ),
    ] = defaults_flag_in_config["triage_database"],
    change_line_prefix: Annotated[
        str,
        typer.Option(
            "--change-line-prefix",
            help="Change the line prefix for the displayed source codes (i.e. file.sol:1).",
            rich_help_panel="Detectors",
        ),
    ] = ":",
    solc_ast: Annotated[bool, typer.Option(hidden=True)] = False,
    json_types: Annotated[
        Optional[str],
        typer.Option(
            help="Types to include in the JSON output.", click_type=CommaSeparatedValueParser()
        ),
    ] = ",".join(DEFAULT_JSON_OUTPUT_TYPES),
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
                """
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
            "--filter-paths",
            help="Regex filter to exclude detector results matching file path e.g. (mocks/|test/).",
            click_type=CommaSeparatedValueParser(),
            rich_help_panel="Filtering",
        ),
    ] = defaults_flag_in_config["filter_paths"],
    include_paths: Annotated[
        Optional[List[str]],
        typer.Option(
            "--include-paths",
            help="Regex filter to include detector results matching file path e.g. (src/|contracts/).",
            click_type=CommaSeparatedValueParser(),
            rich_help_panel="Filtering",
        ),
    ] = defaults_flag_in_config["include_paths"],
):
    """Run detectors and report findings."""

    state = ctx.ensure_object(SlitherState)

    # Handle filter_paths and include_paths from config file
    # These use CommaSeparatedValueParser which has compatibility issues with default_map
    if filter_paths is None:
        config_filter = state.get("filter_paths")
        if config_filter is not None:
            filter_paths = [config_filter] if isinstance(config_filter, str) else config_filter
    if include_paths is None:
        config_include = state.get("include_paths")
        if config_include is not None:
            include_paths = [config_include] if isinstance(config_include, str) else config_include

    # Update the state
    state.update(
        {
            "markdown_root": markdown_root,
            "sarif_input": sarif_input,
            "sarif_triage": sarif_triage,
            "triage_mode": triage_mode,
            "triage_database": triage_database,
            "change_line_prefix": change_line_prefix,
            "generate_patches": generate_patches,
            "filter_paths": filter_paths,
            "include_paths": include_paths,
        }
    )

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

    format_output(
        state.get("output_format"),
        state.get("output_file"),
        slither_instances,
        results_detectors,
        [],
        output_errors,
        runned_detectors=detector_classes,
        json_types=json_types,
        zip_type=state.get("zip_type"),
        checklist=checklist,
        checklist_limit=checklist_limit,
        show_ignored_findings=show_ignored_findings,
        all_detectors=DETECTORS,
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


@app.command(name="print", help="Run printers on the target.")
def printer_command(
    ctx: typer.Context,
    target: target_type,
    list_printers: Annotated[
        Optional[bool],
        typer.Option(
            "--list-printers",
            help="List available printers.",
            callback=list_printers_action,
            rich_help_panel="Printers",
            is_eager=True,
        ),
    ] = False,
    printers_to_run: Annotated[
        Optional[str],
        typer.Option(
            "--print",
            help="Comma-separated list of contract information printers, "
            f"available printers: {', '.join(d.ARGUMENT for d in PRINTERS)}",
            rich_help_panel="Printers",
            autocompletion=complete_printers,
        ),
    ] = defaults_flag_in_config["printers_to_run"],
    no_fail: Annotated[
        bool,
        typer.Option(
            "--no-fail",
            help="Do not fail in case of parsing (echidna mode only).",
            rich_help_panel="Printers",
        ),
    ] = defaults_flag_in_config["no_fail"],
):
    state = ctx.ensure_object(SlitherState)
    state["no_fail"] = no_fail

    choosen_printers = choose_printers(printers_to_run)

    slither_instances, _, results_printers, output_errors, number_contracts = handle_target(
        ctx,
        target,
        printers_to_run=choosen_printers,
    )

    state = ctx.ensure_object(SlitherState)
    format_output(
        output_format=state.get("output_format"),
        output_file=state.get("output_file"),
        slither_instances=slither_instances,
        results_detectors=[],
        results_printers=results_printers,
        output_error=output_errors,
        all_printers=PRINTERS,
    )

    if number_contracts == 0:
        logger.warning(red("No contract was analyzed"))
    else:
        logger.info("%s analyzed (%d contracts)", target.target, number_contracts)


# pylint: disable=too-many-locals
def handle_target(
    ctx: typer.Context,
    target: Target,
    solc_ast: bool = False,
    detectors_to_run: Optional[List[Type[AbstractDetector]]] = None,
    printers_to_run: Optional[List[Type[AbstractPrinter]]] = None,
):
    if detectors_to_run is None:
        detectors_to_run = []

    if printers_to_run is None:
        printers_to_run = []

    state = ctx.ensure_object(SlitherState)

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


@app.callback(invoke_without_command=True, no_args_is_help=True)
def main_callback(
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
        Optional[str],
        typer.Option(
            "--zip",
            hidden=True,
            help="Export the results as a zipped JSON file.",
            rich_help_panel="Formatting",
        ),
    ] = None,
    json_: Annotated[
        Optional[str],
        typer.Option(
            "--json",
            hidden=True,
            help="Print results in JSON format.",
            rich_help_panel="Formatting",
        ),
    ] = None,
    sarif: Annotated[
        Optional[str],
        typer.Option(
            "--sarif",
            hidden=True,
            help="Print results in SARIF format.",
            rich_help_panel="Formatting",
        ),
    ] = None,
    zip_type: Annotated[
        Optional[ZipType],
        typer.Option(
            "--zip-type",
            help="Zip compression type.",
            rich_help_panel="Formatting",
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
    config_file: Annotated[
        Optional[Path],
        typer.Option(
            "--config-file",
            "--config",
            help="Configuration file. Any argument specified on the command line overrides the one "
            "specified in the configuration file.",
            rich_help_panel="Misc",
            show_default="slither.config.json",
        ),
    ] = None,
    debug: Annotated[bool, typer.Option(hidden=True)] = False,
    markdown: Annotated[
        Optional[str], typer.Option(hidden=True, callback=output_markdown_action)
    ] = None,
    wiki_detectors: Annotated[
        Optional[str],
        typer.Option(
            hidden=True,
            help="Print each detectors information that matches the pattern.",
            callback=output_wiki_action,
        ),
    ] = None,
    legacy_ast: Annotated[bool, typer.Option(hidden=True)] = False,
    skip_assembly: Annotated[bool, typer.Option(hidden=True)] = False,
    perf: Annotated[bool, typer.Option(help="Profile slither execution.", hidden=True)] = False,
    disallow_partial: Annotated[bool, typer.Option(hidden=True)] = False,
):
    """Slither is a static Solidity/Vyper/Yul analyzer.

    Maintained by Trail of Bits.
    [https://github.com/crytic/slither](https://github.com/crytic/slither)
    """
    state = ctx.ensure_object(SlitherState)

    if perf:
        print("PERF ENABLED")
        state["perf"] = cProfile.Profile()
        state["perf"].enable()

    # Formatting configuration
    if zip_ or sarif or json_:
        if output_format != OutputFormat.TEXT:
            raise typer.BadParameter("Only specify the output format once.")

        options_set = [bool(zip_), bool(sarif), bool(json_)]
        if options_set.count(True) > 1:
            raise typer.BadParameter("Mutually excluding formatting options set.")

        if zip_ is not None:
            output_format = OutputFormat.ZIP
            output_file = Path(zip_)
        elif sarif is not None:
            output_format = OutputFormat.SARIF
            output_file = Path(sarif)
        elif json_ is not None:
            output_format = OutputFormat.JSON
            output_file = Path(json_)

    if output_format != OutputFormat.TEXT:
        disable_color = True

    set_colorization_enabled(False if disable_color else sys.stdout.isatty())

    if output_format in (OutputFormat.JSON, OutputFormat.SARIF):
        StandardOutputCapture.enable(output_file == Path("-"))

    config = read_config_file(config_file)

    # Set default_map for subcommand parameters from config file
    # Click/Typer will use these as defaults if not provided on command line
    # Note: filter_paths and include_paths are excluded because they use CommaSeparatedValueParser
    # which has compatibility issues with default_map. They are handled in detect() via state.
    ctx.default_map = ctx.default_map or {}
    detect_config_params = {
        "fail_on",
        "detectors_to_run",
        "detectors_to_exclude",
        "exclude_informational",
        "exclude_optimization",
        "exclude_low",
        "exclude_medium",
        "exclude_high",
    }
    detect_defaults = {}
    for k, v in config.items():
        if k in detect_config_params:
            # Convert FailOnLevel enum back to string for Typer validation
            if k == "fail_on" and isinstance(v, FailOnLevel):
                detect_defaults[k] = v.value
            else:
                detect_defaults[k] = v
    ctx.default_map["detect"] = detect_defaults
    ctx.default_map["print"] = {
        k: v for k, v in config.items() if k in {"printers_to_run", "no_fail"}
    }

    log_level = logging.INFO if not debug else logging.DEBUG
    configure_logger(log_level)

    # Update the state with the current
    locals_vars = locals()
    for option in config:
        if option in locals_vars:
            state[option] = locals_vars[option]
        else:
            state[option] = config[option]

    state["output_format"] = output_format
    state["output_file"] = output_file


def configure_logger(log_level: int = logging.INFO):
    """Configure slither loggers."""
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
        logging.getLogger(logger_name).setLevel(log_level)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)

    console_handler.setFormatter(FormatterCryticCompile())

    crytic_compile_error = logging.getLogger("CryticCompile")
    crytic_compile_error.addHandler(console_handler)
    crytic_compile_error.propagate = False
    crytic_compile_error.setLevel(logging.WARNING)


def main():
    """Entry point for the slither CLI."""
    logger.setLevel(logging.INFO)
    # Codebase with complex dominators can lead to a lot of SSA recursive call
    sys.setrecursionlimit(1500)
    app()


if __name__ == "__main__":
    main()
