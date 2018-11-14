import logging
import os
import subprocess
import sys

from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.printers.abstract_printer import AbstractPrinter
from .solc_parsing.slitherSolc import SlitherSolc
from .utils.colors import red

logger = logging.getLogger("Slither")
logging.basicConfig()

logger_detector = logging.getLogger("Detectors")
logger_printer = logging.getLogger("Printers")


class Slither(SlitherSolc):

    def __init__(self, contract, solc='solc', disable_solc_warnings=False, solc_arguments='', ast_format='--ast-json'):
        self._detectors = []
        self._printers = []

        # json text provided
        if isinstance(contract, list):
            super(Slither, self).__init__('')
            for c in contract:
                if 'absolutePath' in c:
                    path = c['absolutePath']
                else:
                    path = c['attributes']['absolutePath']
                self._parse_contracts_from_loaded_json(c, path)
        # .json or .sol provided
        else:
            contracts_json = self._run_solc(contract, solc, disable_solc_warnings, solc_arguments, ast_format)
            super(Slither, self).__init__(contract)

            for c in contracts_json:
                self._parse_contracts_from_json(c)

        self._analyze_contracts()

    @property
    def detectors(self):
        return self._detectors

    @property
    def detectors_high(self):
        return [d for d in self.detectors if d.IMPACT == DetectorClassification.HIGH]

    @property
    def detectors_medium(self):
        return [d for d in self.detectors if d.IMPACT == DetectorClassification.MEDIUM]

    @property
    def detectors_low(self):
        return [d for d in self.detectors if d.IMPACT == DetectorClassification.LOW]

    @property
    def detectors_informational(self):
        return [d for d in self.detectors if d.IMPACT == DetectorClassification.INFORMATIONAL]

    def register_detector(self, detector_class):
        """
        :param detector_class: Class inheriting from `AbstractDetector`.
        """
        self._check_common_things('detector', detector_class, AbstractDetector, self._detectors)

        instance = detector_class(self, logger_detector)
        self._detectors.append(instance)

    def register_printer(self, printer_class):
        """
        :param printer_class: Class inheriting from `AbstractPrinter`.
        """
        self._check_common_things('printer', printer_class, AbstractPrinter, self._printers)

        instance = printer_class(self, logger_printer)
        self._printers.append(instance)

    def run_detectors(self):
        """
        :return: List of registered detectors results.
        """

        return [d.detect() for d in self._detectors]

    def run_printers(self):
        """
        :return: List of registered printers outputs.
        """

        return [p.output(self.filename) for p in self._printers]

    def _check_common_things(self, thing_name, cls, base_cls, instances_list):

        if not issubclass(cls, base_cls) or cls is base_cls:
            raise Exception(
                "You can't register {!r} as a {}. You need to pass a class that inherits from {}".format(
                    cls, thing_name, base_cls.__name__
                )
            )

        if any(isinstance(obj, cls) for obj in instances_list):
            raise Exception(
                "You can't register {!r} twice.".format(cls)
            )

    def _run_solc(self, filename, solc, disable_solc_warnings, solc_arguments, ast_format):
        if not os.path.isfile(filename):
            logger.error('{} does not exist (are you in the correct directory?)'.format(filename))
            exit(-1)
        is_ast_file = False
        if filename.endswith('json'):
            is_ast_file = True
        elif not filename.endswith('.sol'):
            raise Exception('Incorrect file format')

        if is_ast_file:
            with open(filename) as astFile:
                stdout = astFile.read()
                if not stdout:
                    logger.info('Empty AST file: %s', filename)
                    sys.exit(-1)
        else:
            cmd = [solc, filename, ast_format]
            if solc_arguments:
                # To parse, we first split the string on each '--'
                solc_args = solc_arguments.split('--')
                # Split each argument on the first space found
                # One solc option may have multiple argument sepparated with ' '
                # For example: --allow-paths /tmp .
                # split() removes the delimiter, so we add it again
                solc_args = [('--' + x).split(' ', 1) for x in solc_args if x]
                # Flat the list of list
                solc_args = [item for sublist in solc_args for item in sublist]
                cmd += solc_args
            # Add . as default allowed path
            if '--allow-paths' not in cmd:
                cmd += ['--allow-paths', '.']

            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            stdout, stderr = process.communicate()
            stdout, stderr = stdout.decode(), stderr.decode()  # convert bytestrings to unicode strings

            if stderr and (not disable_solc_warnings):
                stderr = stderr.split('\n')
                stderr = [x if 'Error' not in x else red(x) for x in stderr]
                stderr = '\n'.join(stderr)
                logger.info('Compilation warnings/errors on %s:\n%s', filename, stderr)

        stdout = stdout.split('\n=')

        return stdout
