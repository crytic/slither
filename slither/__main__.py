#!/usr/bin/env python3

import sys
import argparse
import logging
import traceback
import os
import glob
import json

from slither.slither import Slither
from slither.detectors.detectors import Detectors
from slither.printers.printers import Printers

logging.basicConfig()
logger = logging.getLogger("Slither")


def determineChecks(detectors, args):
    if args.low:
        return detectors.low
    elif args.medium:
        return detectors.medium + detectors.high
    elif args.high:
        return detectors.high
    elif args.detectors_to_run:
        return args.detectors_to_run
    else:
        return detectors.high + detectors.medium + detectors.low + detectors.code_quality


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


def main():
    detectors = Detectors()
    printers = Printers()

    parser = argparse.ArgumentParser(description='Slither',
                                     usage="slither.py contract.sol [flag]")

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

    parser.add_argument('--low',
                        help='Only low analyses',
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

    for detector_name, Detector in detectors.detectors.items():
        detector_arg = '--{}'.format(Detector.ARGUMENT)
        detector_help = 'Detection of ' + Detector.HELP
        parser.add_argument(detector_arg,
                            help=detector_help,
                            action="append_const",
                            dest="detectors_to_run",
                            const=detector_name)

    for printer_name, Printer in printers.printers.items():
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


if __name__ == '__main__':
    main()
