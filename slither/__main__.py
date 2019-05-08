#!/usr/bin/env python3

import argparse
import glob
import inspect
import json
import logging
import os
import subprocess
import sys
import traceback

from pkg_resources import iter_entry_points, require
from crytic_compile import cryticparser

from slither.detectors import all_detectors
from slither.detectors.abstract_detector import (AbstractDetector,
                                                 DetectorClassification)
from slither.printers import all_printers
from slither.printers.abstract_printer import AbstractPrinter
from slither.slither import Slither
from slither.utils.colors import red, yellow, set_colorization_enabled
from slither.utils.command_line import (output_detectors, output_results_to_markdown,
                                        output_detectors_json, output_printers,
                                        output_to_markdown, output_wiki)
from crytic_compile import is_supported
from slither.exceptions import SlitherException

logging.basicConfig()
logger = logging.getLogger("Slither")

###################################################################################
###################################################################################
# region Process functions
###################################################################################
###################################################################################

def process(filename, args, detector_classes, printer_classes):
    """
    The core high-level code for running Slither static analysis.

    Returns:
        list(result), int: Result list and number of contracts analyzed
    """
    ast = '--ast-compact-json'
    if args.legacy_ast:
        ast = '--ast-json'
    args.filter_paths = parse_filter_paths(args)
    slither = Slither(filename,
                      ast_format=ast,
                      **vars(args))

    return _process(slither, detector_classes, printer_classes)

def _process(slither, detector_classes, printer_classes):
    for detector_cls in detector_classes:
        slither.register_detector(detector_cls)

    for printer_cls in printer_classes:
        slither.register_printer(printer_cls)

    analyzed_contracts_count = len(slither.contracts)

    results = []

    if not printer_classes:
        detector_results = slither.run_detectors()
        detector_results = [x for x in detector_results if x]  # remove empty results
        detector_results = [item for sublist in detector_results for item in sublist]  # flatten

        results.extend(detector_results)

    slither.run_printers()  # Currently printers does not return results

    return results, analyzed_contracts_count


def process_files(filenames, args, detector_classes, printer_classes):
    all_contracts = []

    for filename in filenames:
        with open(filename, encoding='utf8') as f:
            contract_loaded = json.load(f)
            all_contracts.append(contract_loaded['ast'])

    slither = Slither(all_contracts,
                      solc=args.solc,
                      disable_solc_warnings=args.disable_solc_warnings,
                      solc_arguments=args.solc_args,
                      filter_paths=parse_filter_paths(args),
                      triage_mode=args.triage_mode)

    return _process(slither, detector_classes, printer_classes)

# endregion
###################################################################################
###################################################################################
# region Output
###################################################################################
###################################################################################


def wrap_json_stdout(success, error_message, results=None):
    return {
        "success": success,
        "error": error_message,
        "results": results
    }


def output_json(results, filename):
    if filename is None:
        # Write json to console
        print(json.dumps(wrap_json_stdout(True, None, results)))
    else:
        # Write json to file
        if os.path.isfile(filename):
            logger.info(yellow(f'{filename} exists already, the overwrite is prevented'))
        else:
            with open(filename, 'w', encoding='utf8') as f:
                json.dump(results, f, indent=2)

# endregion
###################################################################################
###################################################################################
# region Exit
###################################################################################
###################################################################################

def exit(results):
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
    for entry_point in iter_entry_points(group='slither_analyzer.plugin', name=None):
        make_plugin = entry_point.load()

        plugin_detectors, plugin_printers = make_plugin()

        if not all(issubclass(d, AbstractDetector) for d in plugin_detectors):
            raise Exception('Error when loading plugin %s, %r is not a detector' % (entry_point, d))

        if not all(issubclass(p, AbstractPrinter) for p in plugin_printers):
            raise Exception('Error when loading plugin %s, %r is not a printer' % (entry_point, p))

        # We convert those to lists in case someone returns a tuple
        detectors += list(plugin_detectors)
        printers += list(plugin_printers)

    return detectors, printers

def choose_detectors(args, all_detector_classes):
    # If detectors are specified, run only these ones

    detectors_to_run = []
    detectors = {d.ARGUMENT: d for d in all_detector_classes}

    if args.detectors_to_run == 'all':
        detectors_to_run = all_detector_classes
        if args.detectors_to_exclude:
            detectors_excluded = args.detectors_to_exclude.split(',')
            for d in detectors:
                if d in detectors_excluded:
                    detectors_to_run.remove(detectors[d])
    else:
        for d in args.detectors_to_run.split(','):
            if d in detectors:
                detectors_to_run.append(detectors[d])
            else:
                raise Exception('Error: {} is not a detector'.format(d))
        detectors_to_run = sorted(detectors_to_run, key=lambda x: x.IMPACT)
        return detectors_to_run

    if args.exclude_informational:
        detectors_to_run = [d for d in detectors_to_run if
                            d.IMPACT != DetectorClassification.INFORMATIONAL]
    if args.exclude_low:
        detectors_to_run = [d for d in detectors_to_run if
                            d.IMPACT != DetectorClassification.LOW]
    if args.exclude_medium:
        detectors_to_run = [d for d in detectors_to_run if
                            d.IMPACT != DetectorClassification.MEDIUM]
    if args.exclude_high:
        detectors_to_run = [d for d in detectors_to_run if
                            d.IMPACT != DetectorClassification.HIGH]
    if args.detectors_to_exclude:
        detectors_to_run = [d for d in detectors_to_run if
                            d.ARGUMENT not in args.detectors_to_exclude]

    detectors_to_run = sorted(detectors_to_run, key=lambda x: x.IMPACT)

    return detectors_to_run


def choose_printers(args, all_printer_classes):
    printers_to_run = []

    # disable default printer
    if args.printers_to_run is None:
        return []

    if args.printers_to_run == 'all':
        return all_printer_classes

    printers = {p.ARGUMENT: p for p in all_printer_classes}
    for p in args.printers_to_run.split(','):
        if p in printers:
            printers_to_run.append(printers[p])
        else:
            raise Exception('Error: {} is not a printer'.format(p))
    return printers_to_run

# endregion
###################################################################################
###################################################################################
# region Command line parsing
###################################################################################
###################################################################################

def parse_filter_paths(args):
    if args.filter_paths:
        return args.filter_paths.split(',')
    return []

# Those are the flags shared by the command line and the config file
defaults_flag_in_config = {
    'detectors_to_run': 'all',
    'printers_to_run': None,
    'detectors_to_exclude': None,
    'exclude_informational': False,
    'exclude_low': False,
    'exclude_medium': False,
    'exclude_high': False,
    'solc': 'solc',
    'solc_args': None,
    'disable_solc_warnings': False,
    'json': None,
    'truffle_version': None,
    'disable_color': False,
    'filter_paths': None,
    'truffle_ignore_compile': False,
    'truffle_build_directory': 'build/contracts',
    'embark_ignore_compile': False,
    'embark_overwrite_config': False,
    # debug command
    'legacy_ast': False,
    'ignore_return_value': False
    }

def parse_args(detector_classes, printer_classes):
    parser = argparse.ArgumentParser(description='Slither. For usage information, see https://github.com/crytic/slither/wiki/Usage',
                                     usage="slither.py contract.sol [flag]")

    parser.add_argument('filename',
                        help='contract.sol')

    cryticparser.init(parser)

    parser.add_argument('--version',
                        help='displays the current version',
                        version=require('slither-analyzer')[0].version,
                        action='version')

    group_detector = parser.add_argument_group('Detectors')
    group_printer = parser.add_argument_group('Printers')
    group_misc = parser.add_argument_group('Additional option')

    group_detector.add_argument('--detect',
                                help='Comma-separated list of detectors, defaults to all, '
                                     'available detectors: {}'.format(
                                         ', '.join(d.ARGUMENT for d in detector_classes)),
                                action='store',
                                dest='detectors_to_run',
                                default=defaults_flag_in_config['detectors_to_run'])

    group_printer.add_argument('--print',
                               help='Comma-separated list fo contract information printers, '
                                    'available printers: {}'.format(
                                        ', '.join(d.ARGUMENT for d in printer_classes)),
                               action='store',
                               dest='printers_to_run',
                               default=defaults_flag_in_config['printers_to_run'])

    group_detector.add_argument('--list-detectors',
                                help='List available detectors',
                                action=ListDetectors,
                                nargs=0,
                                default=False)

    group_printer.add_argument('--list-printers',
                               help='List available printers',
                               action=ListPrinters,
                               nargs=0,
                               default=False)

    group_detector.add_argument('--exclude',
                                help='Comma-separated list of detectors that should be excluded',
                                action='store',
                                dest='detectors_to_exclude',
                                default=defaults_flag_in_config['detectors_to_exclude'])

    group_detector.add_argument('--exclude-informational',
                                help='Exclude informational impact analyses',
                                action='store_true',
                                default=defaults_flag_in_config['exclude_informational'])

    group_detector.add_argument('--exclude-low',
                                help='Exclude low impact analyses',
                                action='store_true',
                                default=defaults_flag_in_config['exclude_low'])

    group_detector.add_argument('--exclude-medium',
                                help='Exclude medium impact analyses',
                                action='store_true',
                                default=defaults_flag_in_config['exclude_medium'])

    group_detector.add_argument('--exclude-high',
                                help='Exclude high impact analyses',
                                action='store_true',
                                default=defaults_flag_in_config['exclude_high'])


    group_misc.add_argument('--json',
                            help='Export results as JSON',
                            action='store',
                            default=defaults_flag_in_config['json'])


    group_misc.add_argument('--disable-color',
                            help='Disable output colorization',
                            action='store_true',
                            default=defaults_flag_in_config['disable_color'])

    group_misc.add_argument('--filter-paths',
                            help='Comma-separated list of paths for which results will be excluded',
                            action='store',
                            dest='filter_paths',
                            default=defaults_flag_in_config['filter_paths'])

    group_misc.add_argument('--triage-mode',
                            help='Run triage mode (save results in slither.db.json)',
                            action='store_true',
                            dest='triage_mode',
                            default=False)

    group_misc.add_argument('--config-file',
                            help='Provide a config file (default: slither.config.json)',
                            action='store',
                            dest='config_file',
                            default='slither.config.json')

    group_misc.add_argument('--solc-ast',
                            help='Provide the contract as a json AST',
                            action='store_true',
                            default=False)

    # debugger command
    parser.add_argument('--debug',
                        help=argparse.SUPPRESS,
                        action="store_true",
                        default=False)

    parser.add_argument('--markdown',
                        help=argparse.SUPPRESS,
                        action=OutputMarkdown,
                        default=False)


    group_misc.add_argument('--checklist',
                            help=argparse.SUPPRESS,
                            action='store_true',
                            default=False)

    parser.add_argument('--wiki-detectors',
                        help=argparse.SUPPRESS,
                        action=OutputWiki,
                        default=False)

    parser.add_argument('--list-detectors-json',
                        help=argparse.SUPPRESS,
                        action=ListDetectorsJson,
                        nargs=0,
                        default=False)

    parser.add_argument('--legacy-ast',
                        help=argparse.SUPPRESS,
                        action='store_true',
                        default=defaults_flag_in_config['legacy_ast'])

    parser.add_argument('--ignore-return-value',
                        help=argparse.SUPPRESS,
                        action='store_true',
                        default=defaults_flag_in_config['ignore_return_value'])

    # if the json is splitted in different files
    parser.add_argument('--splitted',
                        help=argparse.SUPPRESS,
                        action='store_true',
                        default=False)

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    args = parser.parse_args()

    if os.path.isfile(args.config_file):
        try:
            with open(args.config_file) as f:
                config = json.load(f)
                for key, elem in config.items():
                    if key not in defaults_flag_in_config:
                        logger.info(yellow('{} has an unknown key: {} : {}'.format(args.config_file, key, elem)))
                        continue
                    if getattr(args, key) == defaults_flag_in_config[key]:
                        setattr(args, key, elem)
        except json.decoder.JSONDecodeError as e:
            logger.error(red('Impossible to read {}, please check the file {}'.format(args.config_file, e)))

    return args

class ListDetectors(argparse.Action):
    def __call__(self, parser, *args, **kwargs):
        detectors, _ = get_detectors_and_printers()
        output_detectors(detectors)
        parser.exit()

class ListDetectorsJson(argparse.Action):
    def __call__(self, parser, *args, **kwargs):
        detectors, _ = get_detectors_and_printers()
        output_detectors_json(detectors)
        parser.exit()

class ListPrinters(argparse.Action):
    def __call__(self, parser, *args, **kwargs):
        _, printers = get_detectors_and_printers()
        output_printers(printers)
        parser.exit()

class OutputMarkdown(argparse.Action):
    def __call__(self, parser, args, values, option_string=None):
        detectors, printers = get_detectors_and_printers()
        output_to_markdown(detectors, printers, values)
        parser.exit()

class OutputWiki(argparse.Action):
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
        #for i, msg in enumerate(record.msg):
        if record.msg.startswith('Compilation warnings/errors on '):
            txt = record.args[1]
            txt = txt.split('\n')
            txt = [red(x) if 'Error' in x else x for x in txt]
            txt = '\n'.join(txt)
            record.args = (record.args[0], txt)
        return super().format(record)

# endregion
###################################################################################
###################################################################################
# region Main
###################################################################################
###################################################################################


def main():
    detectors, printers = get_detectors_and_printers()

    main_impl(all_detector_classes=detectors, all_printer_classes=printers)


def main_impl(all_detector_classes, all_printer_classes):
    """
    :param all_detector_classes: A list of all detectors that can be included/excluded.
    :param all_printer_classes: A list of all printers that can be included.
    """
    args = parse_args(all_detector_classes, all_printer_classes)

    # Set colorization option
    set_colorization_enabled(not args.disable_color)

    # If we are outputting json to stdout, we'll want to disable any logging.
    stdout_json = args.json == "-"
    if stdout_json:
        logging.disable()

    printer_classes = choose_printers(args, all_printer_classes)
    detector_classes = choose_detectors(args, all_detector_classes)

    default_log = logging.INFO if not args.debug else logging.DEBUG

    for (l_name, l_level) in [('Slither', default_log),
                              ('Contract', default_log),
                              ('Function', default_log),
                              ('Node', default_log),
                              ('Parsing', default_log),
                              ('Detectors', default_log),
                              ('FunctionSolc', default_log),
                              ('ExpressionParsing', default_log),
                              ('TypeParsing', default_log),
                              ('SSA_Conversion', default_log),
                              ('Printers', default_log),
                              #('CryticCompile', default_log)
                              ]:
        l = logging.getLogger(l_name)
        l.setLevel(l_level)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    console_handler.setFormatter(FormatterCryticCompile())

    crytic_compile_error = logging.getLogger(('CryticCompile'))
    crytic_compile_error.addHandler(console_handler)
    crytic_compile_error.propagate = False
    crytic_compile_error.setLevel(logging.INFO)

    try:
        filename = args.filename

        globbed_filenames = glob.glob(filename, recursive=True)

        if os.path.isfile(filename) or is_supported(filename):
            (results, number_contracts) = process(filename, args, detector_classes, printer_classes)

        elif os.path.isdir(filename) or len(globbed_filenames) > 0:
            extension = "*.sol" if not args.solc_ast else "*.json"
            filenames = glob.glob(os.path.join(filename, extension))
            if not filenames:
                filenames = globbed_filenames
            number_contracts = 0
            results = []
            if args.splitted and args.solc_ast:
                (results, number_contracts) = process_files(filenames, args, detector_classes, printer_classes)
            else:
                for filename in filenames:
                    (results_tmp, number_contracts_tmp) = process(filename, args, detector_classes, printer_classes)
                    number_contracts += number_contracts_tmp
                    results += results_tmp

        else:
            raise Exception("Unrecognised file/dir path: '#{filename}'".format(filename=filename))

        if args.json:
            output_json(results, None if stdout_json else args.json)
        if args.checklist:
            output_results_to_markdown(results)
        # Dont print the number of result for printers
        if number_contracts == 0:
            logger.warn(red('No contract was analyzed'))
        if printer_classes:
            logger.info('%s analyzed (%d contracts)', filename, number_contracts)
        else:
            logger.info('%s analyzed (%d contracts), %d result(s) found', filename, number_contracts, len(results))
        if args.ignore_return_value:
            return
        exit(results)

    except SlitherException as se:
        # Output our error accordingly, via JSON or logging.
        if stdout_json:
            print(wrap_json_stdout(False, repr(se), []))
        else:
            logging.error(red('Error:'))
            logging.error(red(se))
            logging.error('Please report an issue to https://github.com/crytic/slither/issues')
        sys.exit(-1)

    except Exception:
        # Output our error accordingly, via JSON or logging.
        if stdout_json:
            print(wrap_json_stdout(False, traceback.format_exc(), []))
        else:
            logging.error('Error in %s' % args.filename)
            logging.error(traceback.format_exc())
        sys.exit(-1)



if __name__ == '__main__':
    main()


# endregion