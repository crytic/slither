#!/usr/bin/env python2

import sys
import argparse
import logging
import subprocess
import traceback
import os
import glob
import json

from slither.slither import Slither
from slither.utils.colors import red
from slither.detectors.detectors import Detectors
from slither.printers.printers import Printers

logging.basicConfig()
logger = logging.getLogger("Slither")

def determineChecks(detectors, args):
    if args.medium:
        return detectors.medium + detectors.high
    elif args.high:
        return detectors.high
    elif args.detectors_to_run:
        return args.detectors_to_run
    else:
        return detectors.high + detectors.medium + detectors.low


def process(filename, args, detectors, printers):
    slither = Slither(filename, args.solc, args.disable_solc_warnings, args.solc_args)
    if args.printers_to_run:
        [printers.run_printer(slither, p) for p in args.printers_to_run]
        return []
    else:
        checks = determineChecks(detectors, args)
        results = [detectors.run_detector(slither, c) for c in checks]
        results = [x for x in results if x] # remove empty results
        results = [item for sublist in results for item in sublist] #flatten
        return results

def output_json(results, filename):
    with open(filename, 'w') as f:
        json.dump(results, f)

def exit(results):
    if not results:
        sys.exit(0)
    sys.exit(len(results))

if __name__ == '__main__':

    detectors = Detectors()
    printers = Printers()

    parser = argparse.ArgumentParser(description='Slither',
                                     usage="slither.py contract.sol")

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

    parser.add_argument('--medium',
                        help='Only medium and high analyses',
                        action='store_true',
                        default=False)

    parser.add_argument('--high',
                        help='Only high analyses',
                        action='store_true',
                        default=False)

    parser.add_argument('--json',
                        help='Export results as JSON',
                        action='store',
                        default=None)

    # Analyses available

#    parser.add_argument('--reentrancy',
#                        help='Re-entrancy detection',
#                        action="append_const",
#                        dest="detectors_to_run",
#                        const='detect_reentrancy')
#
#    parser.add_argument('--sim',
#                        help='Variable name similitude detection',
#                        action="append_const",
#                        dest="detectors_to_run",
#                        const='detect_sim')
#
#    parser.add_argument('--const-func',
#                        help='Incorrect constant functions',
#                        action="append_const",
#                        dest="detectors_to_run",
#                        const='detect_constant_function')
#
#    parser.add_argument('--missing-cons',
#                        help='Missing constructor detection',
#                        action="append_const",
#                        dest="detectors_to_run",
#                        const='detect_no_constructor')
#
#    parser.add_argument('--unprotected-func',
#                        help='Unprotected function detection',
#                        action="append_const",
#                        dest="detectors_to_run",
#                        const='detect_unprotected_func')
#
#    parser.add_argument('--unprotected-erc20',
#                        help='Unprotected function detection',
#                        action="append_const",
#                        dest="detectors_to_run",
#                        const='detect_unprotected_erc20')
#
#    parser.add_argument('--event-name',
#                        help='Incorrect event name detection',
#                        action="append_const",
#                        dest="detectors_to_run",
#                        const='detect_incorrect_events_prefix')
#
#    parser.add_argument('--erc20-interface',
#                        help='Incorrect ERC20 interface',
#                        action="append_const",
#                        dest="detectors_to_run",
#                        const='detect_incorrect_erc20_interface')
#
#    parser.add_argument('--uninitialized',
#                        help='Uninitialized state vars detection',
#                        action="append_const",
#                        dest="detectors_to_run",
#                        const='detect_uninitialized')
#
#    parser.add_argument('--unused',
#                        help='Unused state vars detection',
#                        action="append_const",
#                        dest="detectors_to_run",
#                        const='detect_unused')
#
#    parser.add_argument('--mapping-deletion',
#                        help='Mapping deletion detection',
#                        action="append_const",
#                        dest="detectors_to_run",
#                        const='detect_mapping_deletion')
#
#    parser.add_argument('--shadowing',
#                        help='State variables shadowing detection',
#                        action="append_const",
#                        dest="detectors_to_run",
#                        const='detect_state_shadowing')
#
#    parser.add_argument('--shadowing-abstract',
#                        help='State variables shadowing detection from abstract contracts',
#                        action="append_const",
#                        dest="detectors_to_run",
#                        const='detect_state_shadowing_abstract')
#
#    parser.add_argument('--unimplemented-func',
#                        help='Unimplemented function detection',
#                        action="append_const",
#                        dest="detectors_to_run",
#                        const='detect_unimplemented_function')
#
#    parser.add_argument('--tx-origin',
#                        help='tx.origin usage detection',
#                        action="append_const",
#                        dest="detectors_to_run",
#                        const='detect_tx_origin')
#
#    parser.add_argument('--suicidal-func',
#                        help='Suicidal functions detection',
#                        action="append_const",
#                        dest="detectors_to_run",
#                        const='detect_suicidal_function')
#
#    parser.add_argument('--msgValue',
#                        help='Non payable function using msg.value detection (solidity >= 0.4)',
#                        action="append_const",
#                        dest="detectors_to_run",
#                        const='detect_msgValue_non_payable')
#
#    parser.add_argument('--print-summary',
#                        help='Print the summary of the contract',
#                        action="append_const",
#                        dest="detectors_to_run",
#                        const='print_summary')
#
#    parser.add_argument('--print-quick-summary',
#                        help='Print a quick summary of the contract',
#                        action="append_const",
#                        dest="detectors_to_run",
#                        const='print_quick_summary')
#
#    parser.add_argument('--print-inheritance',
#                        help='Print the inheritance graph',
#                        action="append_const",
#                        dest="detectors_to_run",
#                        const='print_inheritance')
#

    for detector_name, Detector in detectors.detectors.iteritems():
        detector_arg = '--{}'.format(Detector.ARGUMENT)
        detector_help = 'Detection of ' + Detector.HELP
        parser.add_argument(detector_arg,
                            help=detector_help,
                            action="append_const",
                            dest="detectors_to_run",
                            const=detector_name)

    for printer_name, Printer in printers.printers.iteritems():
        printer_arg = '--{}'.format(Printer.ARGUMENT)
        printer_help = Printer.HELP
        parser.add_argument(printer_arg,
                            help=printer_help,
                            action="append_const",
                            dest="printers_to_run",
                            const=printer_name)

    # Debug
    parser.add_argument('--debug',
                        help='Debug mode',
                        action="store_true",
                        default=False)

    args = parser.parse_args()
    default_log = logging.INFO
    if args.debug:
        default_log = logging.DEBUG

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
        filename = sys.argv[1]

        if os.path.isfile(filename):
            results = process(filename, args, detectors, printers)
        elif os.path.isdir(filename):
            extension = "*.sol" if not args.solc_ast else "*.json"
            filenames = glob.glob(os.path.join(filename, extension))
            results = [process(filename, args, detectors, printers) for filename in filenames]
            results = [item for sublist in results for item in sublist] #flatten
            #if args.json:
            #    output_json(results, args.json)
            #exit(results)
        else:
            raise Exception("Unrecognised file/dir path: '#{filename}'".format(filename=filename))

        if args.json:
            output_json(results, args.json)
        logger.info('%s analyzed, %d result(s) found', filename, len(results))
        exit(results)


    except Exception as e:
        logging.error('Error in %s'%sys.argv[1])
        logging.error(traceback.format_exc())
        sys.exit(-1)
