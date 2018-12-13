#!/usr/bin/env python3

import argparse
import glob
import json
import logging
import os
import sys
import traceback
import subprocess

from pkg_resources import iter_entry_points, require

from slither.detectors.abstract_detector import (AbstractDetector,
                                                 DetectorClassification)
from slither.printers.abstract_printer import AbstractPrinter
from slither.slither import Slither
from slither.utils.colors import red
from slither.utils.command_line import output_to_markdown, output_detectors, output_printers

logging.basicConfig()
logger = logging.getLogger("Slither")


def process(filename, args, detector_classes, printer_classes):
    """
    The core high-level code for running Slither static analysis.

    Returns:
        list(result), int: Result list and number of contracts analyzed
    """
    ast = '--ast-json'
    if args.compact_ast:
        ast = '--ast-compact-json'
    slither = Slither(filename, args.solc, args.disable_solc_warnings, args.solc_args, ast)

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

def process_truffle(dirname, args, detector_classes, printer_classes):
    cmd = ['truffle','compile']
    logger.info('truffle compile running...')
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    stdout, stderr = process.communicate()
    stdout, stderr = stdout.decode(), stderr.decode()  # convert bytestrings to unicode strings

    logger.info(stdout)

    if stderr:
        logger.error(stderr)

    if not os.path.isdir(os.path.join(dirname, 'build'))\
        or not os.path.isdir(os.path.join(dirname, 'build', 'contracts')):
        logger.info(red('No truffle build directory found, did you run `truffle compile`?'))
        return ([], 0)

    filenames = glob.glob(os.path.join(dirname,'build','contracts', '*.json'))

    all_contracts = []
    all_filenames = []

    for filename in filenames:
        with open(filename) as f:
            contract_loaded = json.load(f)
            all_contracts.append(contract_loaded['ast'])
            all_filenames.append(contract_loaded['sourcePath'])

    slither = Slither(all_contracts, args.solc, args.disable_solc_warnings, args.solc_args)
    return _process(slither, detector_classes, printer_classes)


def output_json(results, filename):
    with open(filename, 'w') as f:
        json.dump(results, f)


def exit(results):
    if not results:
        sys.exit(0)
    sys.exit(len(results))


def get_detectors_and_printers():
    """
    NOTE: This contains just a few detectors and printers that we made public.
    """
    from slither.detectors.examples.backdoor import Backdoor
    from slither.detectors.variables.uninitialized_state_variables import UninitializedStateVarsDetection
    from slither.detectors.variables.uninitialized_storage_variables import UninitializedStorageVars
    from slither.detectors.variables.uninitialized_local_variables import UninitializedLocalVars
    from slither.detectors.attributes.constant_pragma import ConstantPragma
    from slither.detectors.attributes.old_solc import OldSolc
    from slither.detectors.attributes.locked_ether import LockedEther
    from slither.detectors.functions.arbitrary_send import ArbitrarySend
    from slither.detectors.functions.suicidal import Suicidal
    from slither.detectors.functions.complex_function import ComplexFunction
    from slither.detectors.reentrancy.reentrancy import Reentrancy
    from slither.detectors.variables.unused_state_variables import UnusedStateVars
    from slither.detectors.variables.possible_const_state_variables import ConstCandidateStateVars
    from slither.detectors.statements.tx_origin import TxOrigin
    from slither.detectors.statements.assembly import Assembly
    from slither.detectors.operations.low_level_calls import LowLevelCalls
    from slither.detectors.operations.unused_return_values import UnusedReturnValues
    from slither.detectors.naming_convention.naming_convention import NamingConvention
    from slither.detectors.functions.external_function import ExternalFunction
    from slither.detectors.statements.controlled_delegatecall import ControlledDelegateCall
    from slither.detectors.attributes.const_functions import ConstantFunctions
    from slither.detectors.attributes.const_functions import ConstantFunctions
    from slither.detectors.attributes.const_functions import ConstantFunctions
    from slither.detectors.shadowing.abstract import ShadowingAbstractDetection
    from slither.detectors.shadowing.state import StateShadowing

    detectors = [Backdoor,
                 UninitializedStateVarsDetection,
                 UninitializedStorageVars,
                 UninitializedLocalVars,
                 ConstantPragma,
                 OldSolc,
                 Reentrancy,
                 LockedEther,
                 ArbitrarySend,
                 Suicidal,
                 UnusedStateVars,
                 TxOrigin,
                 Assembly,
                 LowLevelCalls,
                 NamingConvention,
                 ConstCandidateStateVars,
                 #ComplexFunction,
                 UnusedReturnValues,
                 ExternalFunction,
                 ControlledDelegateCall,
                 ConstantFunctions,
                 ShadowingAbstractDetection,
                 StateShadowing]

    from slither.printers.summary.function import FunctionSummary
    from slither.printers.summary.contract import ContractSummary
    from slither.printers.inheritance.inheritance import PrinterInheritance
    from slither.printers.inheritance.inheritance_graph import PrinterInheritanceGraph
    from slither.printers.call.call_graph import PrinterCallGraph
    from slither.printers.functions.authorization import PrinterWrittenVariablesAndAuthorization
    from slither.printers.summary.slithir import PrinterSlithIR
    from slither.printers.summary.human_summary import PrinterHumanSummary

    printers = [FunctionSummary,
                ContractSummary,
                PrinterInheritance,
                PrinterInheritanceGraph,
                PrinterCallGraph,
                PrinterWrittenVariablesAndAuthorization,
                PrinterSlithIR,
                PrinterHumanSummary]

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

def main():
    detectors, printers = get_detectors_and_printers()

    main_impl(all_detector_classes=detectors, all_printer_classes=printers)


def main_impl(all_detector_classes, all_printer_classes):
    """
    :param all_detector_classes: A list of all detectors that can be included/excluded.
    :param all_printer_classes: A list of all printers that can be included.
    """
    args = parse_args(all_detector_classes, all_printer_classes)

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
                              ('Printers', default_log)]:
        l = logging.getLogger(l_name)
        l.setLevel(l_level)

    try:
        filename = args.filename

        globbed_filenames = glob.glob(filename, recursive=True)

        if os.path.isfile(filename):
            (results, number_contracts) = process(filename, args, detector_classes, printer_classes)

        elif os.path.isfile(os.path.join(filename, 'truffle.js')) or os.path.isfile(os.path.join(filename, 'truffle-config.js')):
            (results, number_contracts) = process_truffle(filename, args, detector_classes, printer_classes)

        elif os.path.isdir(filename) or len(globbed_filenames) > 0:
            extension = "*.sol" if not args.solc_ast else "*.json"
            filenames = glob.glob(os.path.join(filename, extension))
            if len(filenames) == 0:
                filenames = globbed_filenames
            number_contracts = 0
            results = []
            for filename in filenames:
                (results_tmp, number_contracts_tmp) = process(filename, args, detector_classes, printer_classes)
                number_contracts += number_contracts_tmp
                results += results_tmp


        else:
            raise Exception("Unrecognised file/dir path: '#{filename}'".format(filename=filename))

        if args.json:
            output_json(results, args.json)
        # Dont print the number of result for printers
        if printer_classes:
            logger.info('%s analyzed (%d contracts)', filename, number_contracts)
        else:
            logger.info('%s analyzed (%d contracts), %d result(s) found', filename, number_contracts, len(results))
        exit(results)

    except Exception:
        logging.error('Error in %s' % args.filename)
        logging.error(traceback.format_exc())
        sys.exit(-1)


def parse_args(detector_classes, printer_classes):
    parser = argparse.ArgumentParser(description='Slither',
                                     usage="slither.py contract.sol [flag]")

    parser.add_argument('filename',
                        help='contract.sol')

    parser.add_argument('--version',
                        help='displays the current version',
                        version=require('slither-analyzer')[0].version,
                        action='version')

    group_detector = parser.add_argument_group('Detectors')
    group_printer = parser.add_argument_group('Printers')
    group_solc = parser.add_argument_group('Solc options')
    group_misc = parser.add_argument_group('Additional option')

    group_detector.add_argument('--detect',
                                help='Comma-separated list of detectors, defaults to all, '
                                     'available detectors: {}'.format(
                                         ', '.join(d.ARGUMENT for d in detector_classes)),
                                action='store',
                                dest='detectors_to_run',
                                default='all')

    group_printer.add_argument('--print',
                               help='Comma-separated list fo contract information printers, '
                                    'available printers: {}'.format(
                                        ', '.join(d.ARGUMENT for d in printer_classes)),
                               action='store',
                               dest='printers_to_run',
                               default='')

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
                                default='')

    group_detector.add_argument('--exclude-informational',
                                help='Exclude informational impact analyses',
                                action='store_true',
                                default=False)

    group_detector.add_argument('--exclude-low',
                                help='Exclude low impact analyses',
                                action='store_true',
                                default=False)

    group_detector.add_argument('--exclude-medium',
                                help='Exclude medium impact analyses',
                                action='store_true',
                                default=False)

    group_detector.add_argument('--exclude-high',
                                help='Exclude high impact analyses',
                                action='store_true',
                                default=False)


    group_solc.add_argument('--solc',
                            help='solc path',
                            action='store',
                            default='solc')

    group_solc.add_argument('--solc-args',
                            help='Add custom solc arguments. Example: --solc-args "--allow-path /tmp --evm-version byzantium".',
                            action='store',
                            default=None)

    group_solc.add_argument('--disable-solc-warnings',
                            help='Disable solc warnings',
                            action='store_true',
                            default=False)

    group_solc.add_argument('--solc-ast',
                            help='Provide the ast solc file',
                            action='store_true',
                            default=False)

    group_misc.add_argument('--json',
                            help='Export results as JSON',
                            action='store',
                            default=None)



    # debugger command
    parser.add_argument('--debug',
                        help=argparse.SUPPRESS,
                        action="store_true",
                        default=False)

    parser.add_argument('--markdown',
                        help=argparse.SUPPRESS,
                        action=OutputMarkdown,
                        nargs=0,
                        default=False)

    parser.add_argument('--compact-ast',
                        help=argparse.SUPPRESS,
                        action='store_true',
                        default=False)

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    args = parser.parse_args()

    return args

class ListDetectors(argparse.Action):
    def __call__(self, parser, *args, **kwargs):
        detectors, _ = get_detectors_and_printers()
        output_detectors(detectors)
        parser.exit()

class ListPrinters(argparse.Action):
    def __call__(self, parser, *args, **kwargs):
        _, printers = get_detectors_and_printers()
        output_printers(printers)
        parser.exit()

class OutputMarkdown(argparse.Action):
    def __call__(self, parser, *args, **kwargs):
        detectors, printers = get_detectors_and_printers()
        output_to_markdown(detectors, printers)
        parser.exit()


def choose_detectors(args, all_detector_classes):
    # If detectors are specified, run only these ones

    detectors_to_run = []
    detectors = {d.ARGUMENT: d for d in all_detector_classes}

    if args.detectors_to_run == 'all':
        detectors_to_run = all_detector_classes
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
    if args.printers_to_run == '':
        return []

    printers = {p.ARGUMENT: p for p in all_printer_classes}
    for p in args.printers_to_run.split(','):
        if p in printers:
            printers_to_run.append(printers[p])
        else:
            raise Exception('Error: {} is not a printer'.format(p))
    return printers_to_run


if __name__ == '__main__':
    main()
