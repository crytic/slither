import logging
import os
import subprocess
import sys
import glob
import json

from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.printers.abstract_printer import AbstractPrinter
from .solc_parsing.slitherSolc import SlitherSolc
from .utils.colors import red

logger = logging.getLogger("Slither")
logging.basicConfig()

logger_detector = logging.getLogger("Detectors")
logger_printer = logging.getLogger("Printers")


class Slither(SlitherSolc):

    def __init__(self, contract, **kwargs):
        '''
            Args:
                contract (str| list(json))
            Keyword Args:
                solc (str): solc binary location (default 'solc')
                disable_solc_warnings (bool): True to disable solc warnings (default false)
                solc_argeuments (str): solc arguments (default '')
                ast_format (str): ast format (default '--ast-compact-json')
                is_truffle (bool): is a truffle directory (default false)
                filter_paths (list(str)): list of path to filter (default [])
                interactive_mode (bool): if true, switch to interactive mode (default false)
        '''

        is_truffle = kwargs.get('is_truffle', False)

        # truffle directory
        if is_truffle:
            self._init_from_truffle(contract)
        # list of files provided (see --splitted option)
        elif isinstance(contract, list):
            self._init_from_list(contract)
        # .json or .sol provided
        else:
            self._init_from_solc(contract, **kwargs)

        self._detectors = []
        self._printers = []

        filter_paths = kwargs.get('filter_paths', [])
        for p in filter_paths:
            self.add_path_to_filter(p)

        interactive_mode = kwargs.get('interactive_mode', False)
        self._interactive_mode = interactive_mode

        self._analyze_contracts()

    def _init_from_truffle(self, contract):
        if not os.path.isdir(os.path.join(contract, 'build'))\
            or not os.path.isdir(os.path.join(contract, 'build', 'contracts')):
            logger.info(red('No truffle build directory found, did you run `truffle compile`?'))
            sys.exit(-1)
        super(Slither, self).__init__('')
        filenames = glob.glob(os.path.join(contract, 'build', 'contracts', '*.json'))
        for filename in filenames:
            with open(filename, encoding='utf8') as f:
                contract_loaded = json.load(f)
                contract_loaded = contract_loaded['ast']
                if 'absolutePath' in contract_loaded:
                    path = contract_loaded['absolutePath']
                else:
                    path = contract_loaded['attributes']['absolutePath']
                self._parse_contracts_from_loaded_json(contract_loaded, path)

    def _init_from_solc(self, contract, **kwargs):
        solc = kwargs.get('solc', 'solc')
        disable_solc_warnings = kwargs.get('disable_solc_warnings', False)
        solc_arguments = kwargs.get('solc_arguments', '')
        ast_format = kwargs.get('ast_format', '--ast-compact-json')

        contracts_json = self._run_solc(contract,
                                        solc,
                                        disable_solc_warnings,
                                        solc_arguments,
                                        ast_format)
        super(Slither, self).__init__(contract)

        for c in contracts_json:
            self._parse_contracts_from_json(c)

    def _init_from_list(self, contract):
        super(Slither, self).__init__('')
        for c in contract:
            if 'absolutePath' in c:
                path = c['absolutePath']
            else:
                path = c['attributes']['absolutePath']
            self._parse_contracts_from_loaded_json(c, path)

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

        self.load_previous_results()
        results = [d.detect() for d in self._detectors]
        self.write_results_to_hide()
        return results

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
            with open(filename, encoding='utf8') as astFile:
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

    @property
    def interactive_mode(self):
        return self._interactive_mode
