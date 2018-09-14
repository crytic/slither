#!/usr/bin/env python3

import argparse
import glob
import json
import logging
import os
import sys
import traceback

from pkg_resources import iter_entry_points

from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.printers.abstract_printer import AbstractPrinter
from slither.slither import Slither

logging.basicConfig()
logger = logging.getLogger("Slither")


def process(filename, args, detector_classes, printer_classes):
    """
    The core high-level code for running Slither static analysis.

    Returns:
        list(result), int: Result list and number of contracts analyzed
    """
    slither = Slither(filename, args.solc, args.disable_solc_warnings, args.solc_args)

    for detector_cls in detector_classes:
        slither.register_detector(detector_cls)

    for printer_cls in printer_classes:
        slither.register_printer(printer_cls)

    analyzed_contracts_count = len(slither.contracts)

    results = []

    if printer_classes:
        slither.run_printers()  # Currently printers does not return results

    if detector_classes:
        detector_results = slither.run_detectors()
        detector_results = [x for x in detector_results if x]  # remove empty results
        detector_results = [item for sublist in detector_results for item in sublist]  # flatten

        results.extend(detector_results)

    return results, analyzed_contracts_count


def output_json(results, filename):
    with open(filename, 'w') as f:
        json.dump(results, f)


def exit(results):
    if not results:
        sys.exit(0)
    sys.exit(len(results))


def main():
    """
    NOTE: This contains just a few detectors and printers that we made public.
    """
    from slither.detectors.examples.backdoor import Backdoor
    from slither.detectors.variables.uninitialized_state_variables import UninitializedStateVarsDetection
    from slither.detectors.attributes.constant_pragma import ConstantPragma
    from slither.detectors.attributes.old_solc import OldSolc
    from slither.detectors.reentrancy.reentrancy import Reentrancy
    from slither.detectors.variables.uninitialized_storage_variables import UninitializedStorageVars
    from slither.detectors.statements.tx_origin import TxOrigin

    detectors = [Backdoor,
                 UninitializedStateVarsDetection,
                 ConstantPragma,
                 OldSolc,
                 Reentrancy,
                 UninitializedStorageVars,
                 TxOrigin]

    from slither.printers.summary.summary import PrinterSummary
    from slither.printers.summary.quick_summary import PrinterQuickSummary
    from slither.printers.inheritance.inheritance import PrinterInheritance
    from slither.printers.functions.authorization import PrinterWrittenVariablesAndAuthorization

    printers = [PrinterSummary, PrinterQuickSummary, PrinterInheritance, PrinterWrittenVariablesAndAuthorization]

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

    main_impl(all_detector_classes=detectors, all_printer_classes=printers)


def main_impl(all_detector_classes, all_printer_classes):
    """
    :param all_detector_classes: A list of all detectors that can be included/excluded.
    :param all_printer_classes: A list of all printers that can be included.
    """
    args = parse_args(all_detector_classes, all_printer_classes)

    detector_classes = choose_detectors(args, all_detector_classes)
    printer_classes = choose_printers(args, all_printer_classes)

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
                              ('Printers', default_log)]:
        l = logging.getLogger(l_name)
        l.setLevel(l_level)

    try:
        filename = args.filename

        if os.path.isfile(filename):
            (results, number_contracts) = process(filename, args, detector_classes, printer_classes)

        elif os.path.isdir(filename):
            extension = "*.sol" if not args.solc_ast else "*.json"
            filenames = glob.glob(os.path.join(filename, extension))
            number_contracts = 0
            results = []
            for filename in filenames:
                (results_tmp, number_contracts_tmp) = process(filename, args, detector_classes, printer_classes)
                number_contracts += number_contracts_tmp
                results += results_tmp
            # if args.json:
            #    output_json(results, args.json)
            # exit(results)

        else:
            raise Exception("Unrecognised file/dir path: '#{filename}'".format(filename=filename))

        if args.json:
            output_json(results, args.json)
        logger.info('%s analyzed (%d contracts), %d result(s) found', filename, number_contracts, len(results))
        exit(results)

    except Exception:
        logging.error('Error in %s' % args.filename)
        logging.error(traceback.format_exc())
        sys.exit(-1)


def parse_args(detector_classes, printer_classes):
    parser = argparse.ArgumentParser(description='Slither',
                                     usage="slither.py contract.sol [flag]",
                                     formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=35))

    parser.add_argument('filename',
                        help='contract.sol file')

    parser.add_argument('--solc',
                        help='solc path',
                        action='store',
                        default='solc')

    parser.add_argument('--solc-args',
                        help='Add custom solc arguments. Example: --solc-args "--allow-path /tmp --evm-version byzantium".',
                        action='store',
                        default=None)

    parser.add_argument('--disable-solc-warnings',
                        help='Disable solc warnings',
                        action='store_true',
                        default=False)

    parser.add_argument('--solc-ast',
                        help='Provide the ast solc file',
                        action='store_true',
                        default=False)

    parser.add_argument('--json',
                        help='Export results as JSON',
                        action='store',
                        default=None)

    parser.add_argument('--exclude-informational',
                        help='Exclude informational impact analyses',
                        action='store_true',
                        default=False)

    parser.add_argument('--exclude-low',
                        help='Exclude low impact analyses',
                        action='store_true',
                        default=False)

    parser.add_argument('--exclude-medium',
                        help='Exclude medium impact analyses',
                        action='store_true',
                        default=False)

    parser.add_argument('--exclude-high',
                        help='Exclude high impact analyses',
                        action='store_true',
                        default=False)

    for detector_cls in detector_classes:
        detector_arg = '--detect-{}'.format(detector_cls.ARGUMENT)
        detector_help = 'Detection of {}'.format(detector_cls.HELP)
        parser.add_argument(detector_arg,
                            help=detector_help,
                            action="append_const",
                            dest="detectors_to_run",
                            const=detector_cls.ARGUMENT)

    # Second loop so that the --exclude are shown after all the detectors
    for detector_cls in detector_classes:
        exclude_detector_arg = '--exclude-{}'.format(detector_cls.ARGUMENT)
        exclude_detector_help = 'Exclude {} detector'.format(detector_cls.ARGUMENT)
        parser.add_argument(exclude_detector_arg,
                            help=exclude_detector_help,
                            action="append_const",
                            dest="detectors_to_exclude",
                            const=detector_cls.ARGUMENT)

    for printer_cls in printer_classes:
        printer_arg = '--printer-{}'.format(printer_cls.ARGUMENT)
        printer_help = 'Print {}'.format(printer_cls.HELP)
        parser.add_argument(printer_arg,
                            help=printer_help,
                            action="append_const",
                            dest="printers_to_run",
                            const=printer_cls.ARGUMENT)

    parser.add_argument('--debug',
                        help='Debug mode',
                        action="store_true",
                        default=False)

    return parser.parse_args()


def choose_detectors(args, all_detector_classes):
    # If detectors are specified, run only these ones
    if args.detectors_to_run:
        return [d for d in all_detector_classes if d.ARGUMENT in args.detectors_to_run]

    detectors_to_run = all_detector_classes

    if args.exclude_informational:
        detectors_to_run = [d for d in detectors_to_run if
                            d.CLASSIFICATION != DetectorClassification.CODE_QUALITY]
    if args.exclude_low:
        detectors_to_run = [d for d in detectors_to_run if
                            d.CLASSIFICATION != DetectorClassification.LOW]
    if args.exclude_medium:
        detectors_to_run = [d for d in detectors_to_run if
                            d.CLASSIFICATION != DetectorClassification.MEDIUM]
    if args.exclude_high:
        detectors_to_run = [d for d in detectors_to_run if
                            d.CLASSIFICATION != DetectorClassification.HIGH]
    if args.detectors_to_exclude:
        detectors_to_run = [d for d in detectors_to_run if
                            d.ARGUMENT not in args.detectors_to_exclude]
    return detectors_to_run


def choose_printers(args, all_printer_classes):
    # by default, dont run any printer
    printers_to_run = []
    if args.printers_to_run:
        printers_to_run = [p for p in all_printer_classes if
                           p.ARGUMENT in args.printers_to_run]
    return printers_to_run


if __name__ == '__main__':
    main()
