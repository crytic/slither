#!/usr/bin/env python3

import argparse
import glob
import inspect
import json
import logging
import os
import sys
import traceback

from pkg_resources import iter_entry_points, require

from crytic_compile import cryticparser
from crytic_compile.platform.standard import generate_standard_export
from crytic_compile import compile_all, is_supported

from slither.detectors import all_detectors
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.printers import all_printers
from slither.printers.abstract_printer import AbstractPrinter
from slither.slither import Slither
from slither.utils.output import output_to_json, output_to_zip, ZIP_TYPES_ACCEPTED
from slither.utils.output_capture import StandardOutputCapture
from slither.utils.colors import red, blue, set_colorization_enabled
from slither.utils.command_line import (
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
)
from slither.exceptions import SlitherException

logging.basicConfig()
logger = logging.getLogger("Slither")


###################################################################################
###################################################################################
# region Process functions
###################################################################################
###################################################################################


def process_single(target, args, detector_classes, printer_classes):
    """
    The core high-level code for running Slither static analysis.

    Returns:
        list(result), int: Result list and number of contracts analyzed
    """
    ast = "--ast-compact-json"
    if args.legacy_ast:
        ast = "--ast-json"
    slither = Slither(target, ast_format=ast, **vars(args))

    return _process(slither, detector_classes, printer_classes)


def process_all(target, args, detector_classes, printer_classes):
    compilations = compile_all(target, **vars(args))
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
        ) = process_single(compilation, args, detector_classes, printer_classes)
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


def _process(slither, detector_classes, printer_classes):
    for detector_cls in detector_classes:
        slither.register_detector(detector_cls)

    for printer_cls in printer_classes:
        slither.register_printer(printer_cls)

    analyzed_contracts_count = len(slither.contracts)

    results_detectors = []
    results_printers = []

    if not printer_classes:
        detector_results = slither.run_detectors()
        detector_results = [x for x in detector_results if x]  # remove empty results
        detector_results = [item for sublist in detector_results for item in sublist]  # flatten
        results_detectors.extend(detector_results)

    else:
        printer_results = slither.run_printers()
        printer_results = [x for x in printer_results if x]  # remove empty results
        results_printers.extend(printer_results)

    return slither, results_detectors, results_printers, analyzed_contracts_count


def process_from_asts(filenames, args, detector_classes, printer_classes):
    all_contracts = []

    for filename in filenames:
        with open(filename, encoding="utf8") as file_open:
            contract_loaded = json.load(file_open)
            all_contracts.append(contract_loaded["ast"])

    return process_single(all_contracts, args, detector_classes, printer_classes)


# endregion
###################################################################################
###################################################################################
# region Exit
###################################################################################
###################################################################################


def my_exit(results):
    if not results:
        sys.exit(0)
    sys.exit(len(results))


# endregion
###################################################################################
###################################################################################
# region Detectors and printers
###################################################################################
###################################################################################


def get_detectors_and_printers():
    """
    NOTE: This contains just a few detectors and printers that we made public.
    """

    detectors = [getattr(all_detectors, name) for name in dir(all_detectors)]
    detectors = [d for d in detectors if inspect.isclass(d) and issubclass(d, AbstractDetector)]

    printers = [getattr(all_printers, name) for name in dir(all_printers)]
    printers = [p for p in printers if inspect.isclass(p) and issubclass(p, AbstractPrinter)]

    # Handle plugins!
    for entry_point in iter_entry_points(group="slither_analyzer.plugin", name=None):
        make_plugin = entry_point.load()

        plugin_detectors, plugin_printers = make_plugin()

        detector = None
        if not all(issubclass(detector, AbstractDetector) for detector in plugin_detectors):
            raise Exception(
                "Error when loading plugin %s, %r is not a detector" % (entry_point, detector)
            )
        printer = None
        if not all(issubclass(printer, AbstractPrinter) for printer in plugin_printers):
            raise Exception(
                "Error when loading plugin %s, %r is not a printer" % (entry_point, printer)
            )

        # We convert those to lists in case someone returns a tuple
        detectors += list(plugin_detectors)
        printers += list(plugin_printers)

    return detectors, printers


# pylint: disable=too-many-branches
def choose_detectors(args, all_detector_classes):
    # If detectors are specified, run only these ones

    detectors_to_run = []
    detectors = {d.ARGUMENT: d for d in all_detector_classes}

    if args.detectors_to_run == "all":
        detectors_to_run = all_detector_classes
        if args.detectors_to_exclude:
            detectors_excluded = args.detectors_to_exclude.split(",")
            for detector in detectors:
                if detector in detectors_excluded:
                    detectors_to_run.remove(detectors[detector])
    else:
        for detector in args.detectors_to_run.split(","):
            if detector in detectors:
                detectors_to_run.append(detectors[detector])
            else:
                raise Exception("Error: {} is not a detector".format(detector))
        detectors_to_run = sorted(detectors_to_run, key=lambda x: x.IMPACT)
        return detectors_to_run

    if args.exclude_optimization:
        detectors_to_run = [
            d for d in detectors_to_run if d.IMPACT != DetectorClassification.OPTIMIZATION
        ]

    if args.exclude_informational:
        detectors_to_run = [
            d for d in detectors_to_run if d.IMPACT != DetectorClassification.INFORMATIONAL
        ]
    if args.exclude_low:
        detectors_to_run = [d for d in detectors_to_run if d.IMPACT != DetectorClassification.LOW]
    if args.exclude_medium:
        detectors_to_run = [
            d for d in detectors_to_run if d.IMPACT != DetectorClassification.MEDIUM
        ]
    if args.exclude_high:
        detectors_to_run = [d for d in detectors_to_run if d.IMPACT != DetectorClassification.HIGH]
    if args.detectors_to_exclude:
        detectors_to_run = [
            d for d in detectors_to_run if d.ARGUMENT not in args.detectors_to_exclude
        ]

    detectors_to_run = sorted(detectors_to_run, key=lambda x: x.IMPACT)

    return detectors_to_run


def choose_printers(args, all_printer_classes):
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
            raise Exception("Error: {} is not a printer".format(printer))
    return printers_to_run


# endregion
###################################################################################
###################################################################################
# region Command line parsing
###################################################################################
###################################################################################


def parse_filter_paths(args):
    if args.filter_paths:
        return args.filter_paths.split(",")
    return []


def parse_args(detector_classes, printer_classes):
    parser = argparse.ArgumentParser(
        description="Slither. For usage information, see https://github.com/crytic/slither/wiki/Usage",
        usage="slither.py contract.sol [flag]",
    )

    parser.add_argument("filename", help="contract.sol")

    cryticparser.init(parser)

    parser.add_argument(
        "--version",
        help="displays the current version",
        version=require("slither-analyzer")[0].version,
        action="version",
    )

    group_detector = parser.add_argument_group("Detectors")
    group_printer = parser.add_argument_group("Printers")
    group_misc = parser.add_argument_group("Additional options")

    group_detector.add_argument(
        "--detect",
        help="Comma-separated list of detectors, defaults to all, "
        "available detectors: {}".format(", ".join(d.ARGUMENT for d in detector_classes)),
        action="store",
        dest="detectors_to_run",
        default=defaults_flag_in_config["detectors_to_run"],
    )

    group_printer.add_argument(
        "--print",
        help="Comma-separated list fo contract information printers, "
        "available printers: {}".format(", ".join(d.ARGUMENT for d in printer_classes)),
        action="store",
        dest="printers_to_run",
        default=defaults_flag_in_config["printers_to_run"],
    )

    group_detector.add_argument(
        "--list-detectors",
        help="List available detectors",
        action=ListDetectors,
        nargs=0,
        default=False,
    )

    group_printer.add_argument(
        "--list-printers",
        help="List available printers",
        action=ListPrinters,
        nargs=0,
        default=False,
    )

    group_detector.add_argument(
        "--exclude",
        help="Comma-separated list of detectors that should be excluded",
        action="store",
        dest="detectors_to_exclude",
        default=defaults_flag_in_config["detectors_to_exclude"],
    )

    group_detector.add_argument(
        "--exclude-dependencies",
        help="Exclude results that are only related to dependencies",
        action="store_true",
        default=defaults_flag_in_config["exclude_dependencies"],
    )

    group_detector.add_argument(
        "--exclude-optimization",
        help="Exclude optimization analyses",
        action="store_true",
        default=defaults_flag_in_config["exclude_optimization"],
    )

    group_detector.add_argument(
        "--exclude-informational",
        help="Exclude informational impact analyses",
        action="store_true",
        default=defaults_flag_in_config["exclude_informational"],
    )

    group_detector.add_argument(
        "--exclude-low",
        help="Exclude low impact analyses",
        action="store_true",
        default=defaults_flag_in_config["exclude_low"],
    )

    group_detector.add_argument(
        "--exclude-medium",
        help="Exclude medium impact analyses",
        action="store_true",
        default=defaults_flag_in_config["exclude_medium"],
    )

    group_detector.add_argument(
        "--exclude-high",
        help="Exclude high impact analyses",
        action="store_true",
        default=defaults_flag_in_config["exclude_high"],
    )

    group_misc.add_argument(
        "--json",
        help='Export the results as a JSON file ("--json -" to export to stdout)',
        action="store",
        default=defaults_flag_in_config["json"],
    )

    group_misc.add_argument(
        "--json-types",
        help="Comma-separated list of result types to output to JSON, defaults to "
        + f'{",".join(output_type for output_type in DEFAULT_JSON_OUTPUT_TYPES)}. '
        + f'Available types: {",".join(output_type for output_type in JSON_OUTPUT_TYPES)}',
        action="store",
        default=defaults_flag_in_config["json-types"],
    )

    group_misc.add_argument(
        "--zip",
        help="Export the results as a zipped JSON file",
        action="store",
        default=defaults_flag_in_config["zip"],
    )

    group_misc.add_argument(
        "--zip-type",
        help=f'Zip compression type. One of {",".join(ZIP_TYPES_ACCEPTED.keys())}. Default lzma',
        action="store",
        default=defaults_flag_in_config["zip_type"],
    )

    group_misc.add_argument(
        "--markdown-root", help="URL for markdown generation", action="store", default="",
    )

    group_misc.add_argument(
        "--disable-color",
        help="Disable output colorization",
        action="store_true",
        default=defaults_flag_in_config["disable_color"],
    )

    group_misc.add_argument(
        "--filter-paths",
        help="Comma-separated list of paths for which results will be excluded",
        action="store",
        dest="filter_paths",
        default=defaults_flag_in_config["filter_paths"],
    )

    group_misc.add_argument(
        "--triage-mode",
        help="Run triage mode (save results in slither.db.json)",
        action="store_true",
        dest="triage_mode",
        default=False,
    )

    group_misc.add_argument(
        "--config-file",
        help="Provide a config file (default: slither.config.json)",
        action="store",
        dest="config_file",
        default="slither.config.json",
    )

    group_misc.add_argument(
        "--solc-ast", help="Provide the contract as a json AST", action="store_true", default=False,
    )

    group_misc.add_argument(
        "--generate-patches",
        help="Generate patches (json output only)",
        action="store_true",
        default=False,
    )

    # debugger command
    parser.add_argument("--debug", help=argparse.SUPPRESS, action="store_true", default=False)

    parser.add_argument("--markdown", help=argparse.SUPPRESS, action=OutputMarkdown, default=False)

    group_misc.add_argument(
        "--checklist", help=argparse.SUPPRESS, action="store_true", default=False
    )

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
        "--ignore-return-value",
        help=argparse.SUPPRESS,
        action="store_true",
        default=defaults_flag_in_config["ignore_return_value"],
    )

    # if the json is splitted in different files
    parser.add_argument("--splitted", help=argparse.SUPPRESS, action="store_true", default=False)

    # Disable the throw/catch on partial analyses
    parser.add_argument(
        "--disallow-partial", help=argparse.SUPPRESS, action="store_true", default=False
    )

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    args = parser.parse_args()
    read_config_file(args)

    args.filter_paths = parse_filter_paths(args)

    # Verify our json-type output is valid
    args.json_types = set(args.json_types.split(","))
    for json_type in args.json_types:
        if json_type not in JSON_OUTPUT_TYPES:
            raise Exception(f'Error: "{json_type}" is not a valid JSON result output type.')

    return args


class ListDetectors(argparse.Action):  # pylint: disable=too-few-public-methods
    def __call__(self, parser, *args, **kwargs):  # pylint: disable=signature-differs
        detectors, _ = get_detectors_and_printers()
        output_detectors(detectors)
        parser.exit()


class ListDetectorsJson(argparse.Action):  # pylint: disable=too-few-public-methods
    def __call__(self, parser, *args, **kwargs):  # pylint: disable=signature-differs
        detectors, _ = get_detectors_and_printers()
        detector_types_json = output_detectors_json(detectors)
        print(json.dumps(detector_types_json))
        parser.exit()


class ListPrinters(argparse.Action):  # pylint: disable=too-few-public-methods
    def __call__(self, parser, *args, **kwargs):  # pylint: disable=signature-differs
        _, printers = get_detectors_and_printers()
        output_printers(printers)
        parser.exit()


class OutputMarkdown(argparse.Action):  # pylint: disable=too-few-public-methods
    def __call__(self, parser, args, values, option_string=None):
        detectors, printers = get_detectors_and_printers()
        output_to_markdown(detectors, printers, values)
        parser.exit()


class OutputWiki(argparse.Action):  # pylint: disable=too-few-public-methods
    def __call__(self, parser, args, values, option_string=None):
        detectors, _ = get_detectors_and_printers()
        output_wiki(detectors, values)
        parser.exit()


# endregion
###################################################################################
###################################################################################
# region CustomFormatter
###################################################################################
###################################################################################


class FormatterCryticCompile(logging.Formatter):
    def format(self, record):
        # for i, msg in enumerate(record.msg):
        if record.msg.startswith("Compilation warnings/errors on "):
            txt = record.args[1]
            txt = txt.split("\n")
            txt = [red(x) if "Error" in x else x for x in txt]
            txt = "\n".join(txt)
            record.args = (record.args[0], txt)
        return super().format(record)


# endregion
###################################################################################
###################################################################################
# region Main
###################################################################################
###################################################################################


def main():
    # Codebase with complex domninators can lead to a lot of SSA recursive call
    sys.setrecursionlimit(1500)

    detectors, printers = get_detectors_and_printers()

    main_impl(all_detector_classes=detectors, all_printer_classes=printers)


# pylint: disable=too-many-statements,too-many-branches,too-many-locals
def main_impl(all_detector_classes, all_printer_classes):
    """
    :param all_detector_classes: A list of all detectors that can be included/excluded.
    :param all_printer_classes: A list of all printers that can be included.
    """
    # Set logger of Slither to info, to catch warnings related to the arg parsing
    logger.setLevel(logging.INFO)
    args = parse_args(all_detector_classes, all_printer_classes)

    # Set colorization option
    set_colorization_enabled(not args.disable_color)

    # Define some variables for potential JSON output
    json_results = {}
    output_error = None
    outputting_json = args.json is not None
    outputting_json_stdout = args.json == "-"
    outputting_zip = args.zip is not None
    if args.zip_type not in ZIP_TYPES_ACCEPTED.keys():
        to_log = f'Zip type not accepted, it must be one of {",".join(ZIP_TYPES_ACCEPTED.keys())}'
        logger.error(to_log)

    # If we are outputting JSON, capture all standard output. If we are outputting to stdout, we block typical stdout
    # output.
    if outputting_json:
        StandardOutputCapture.enable(outputting_json_stdout)

    printer_classes = choose_printers(args, all_printer_classes)
    detector_classes = choose_detectors(args, all_detector_classes)

    default_log = logging.INFO if not args.debug else logging.DEBUG

    for (l_name, l_level) in [
        ("Slither", default_log),
        ("Contract", default_log),
        ("Function", default_log),
        ("Node", default_log),
        ("Parsing", default_log),
        ("Detectors", default_log),
        ("FunctionSolc", default_log),
        ("ExpressionParsing", default_log),
        ("TypeParsing", default_log),
        ("SSA_Conversion", default_log),
        ("Printers", default_log),
        # ('CryticCompile', default_log)
    ]:
        logger_level = logging.getLogger(l_name)
        logger_level.setLevel(l_level)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    console_handler.setFormatter(FormatterCryticCompile())

    crytic_compile_error = logging.getLogger(("CryticCompile"))
    crytic_compile_error.addHandler(console_handler)
    crytic_compile_error.propagate = False
    crytic_compile_error.setLevel(logging.INFO)

    results_detectors = []
    results_printers = []
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
            if args.splitted:
                (
                    slither_instance,
                    results_detectors,
                    results_printers,
                    number_contracts,
                ) = process_from_asts(filenames, args, detector_classes, printer_classes)
                slither_instances.append(slither_instance)
            else:
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
        if outputting_json or outputting_zip:
            # Add our compilation information to JSON
            if "compilations" in args.json_types:
                compilation_results = []
                for slither_instance in slither_instances:
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
            output_results_to_markdown(results_detectors)

        # Dont print the number of result for printers
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

        logger.info(
            blue(
                "Use https://crytic.io/ to get access to additional detectors and Github integration"
            )
        )
        if args.ignore_return_value:
            return

    except SlitherException as slither_exception:
        output_error = str(slither_exception)
        traceback.print_exc()
        logging.error(red("Error:"))
        logging.error(red(output_error))
        logging.error("Please report an issue to https://github.com/crytic/slither/issues")

    except Exception:  # pylint: disable=broad-except
        output_error = traceback.format_exc()
        logging.error(traceback.print_exc())
        logging.error(f"Error in {args.filename}")  # pylint: disable=logging-fstring-interpolation
        logging.error(output_error)

    # If we are outputting JSON, capture the redirected output and disable the redirect to output the final JSON.
    if outputting_json:
        if "console" in args.json_types:
            json_results["console"] = {
                "stdout": StandardOutputCapture.get_stdout_output(),
                "stderr": StandardOutputCapture.get_stderr_output(),
            }
        StandardOutputCapture.disable()
        output_to_json(None if outputting_json_stdout else args.json, output_error, json_results)

    if outputting_zip:
        output_to_zip(args.zip, output_error, json_results, args.zip_type)

    # Exit with the appropriate status code
    if output_error:
        sys.exit(-1)
    else:
        my_exit(results_detectors)


if __name__ == "__main__":
    main()

# endregion
