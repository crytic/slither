import logging
import os
import subprocess
import sys
import glob
import json
import platform

from crytic_compile import CryticCompile

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
                filter_paths (list(str)): list of path to filter (default [])
                triage_mode (bool): if true, switch to triage mode (default false)

                truffle_ignore (bool): ignore truffle.js presence (default false)
                truffle_build_directory (str): build truffle directory (default 'build/contracts')
                truffle_ignore_compile (bool): do not run truffle compile (default False)
                truffle_version (str): use a specific truffle version (default None)

                embark_ignore (bool): ignore embark.js presence (default false)
                embark_ignore_compile (bool): do not run embark build (default False)
                embark_overwrite_config (bool): overwrite original config file (default false)

        '''

        truffle_ignore = kwargs.get('truffle_ignore', False)
        embark_ignore = kwargs.get('embark_ignore', False)

        # list of files provided (see --splitted option)
        if isinstance(contract, list):
            self._init_from_list(contract)
        elif contract.endswith('.json'):
            self._init_from_raw_json(contract)
        else:
            super(Slither, self).__init__('')
            cryticCompile = CryticCompile(contract, **kwargs)
            for path, ast in cryticCompile.asts.items():
                self._parse_contracts_from_loaded_json(ast, path)

        self._detectors = []
        self._printers = []

        filter_paths = kwargs.get('filter_paths', [])
        for p in filter_paths:
            self.add_path_to_filter(p)

        triage_mode = kwargs.get('triage_mode', False)
        self._triage_mode = triage_mode

        self._analyze_contracts()

    def _init_from_raw_json(self, filename):
        if not os.path.isfile(filename):
            logger.error('{} does not exist (are you in the correct directory?)'.format(filename))
            exit(-1)
        assert filename.endswith('json')
        with open(filename, encoding='utf8') as astFile:
            stdout = astFile.read()
            if not stdout:
                logger.info('Empty AST file: %s', filename)
                sys.exit(-1)
        contracts_json = stdout.split('\n=')

        super(Slither, self).__init__(filename)

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
        assert filename.endswith('json')
        with open(filename, encoding='utf8') as astFile:
            stdout = astFile.read()
            if not stdout:
                logger.info('Empty AST file: %s', filename)
                sys.exit(-1)
        stdout = stdout.split('\n=')

        return stdout

    @property
    def triage_mode(self):
        return self._triage_mode
