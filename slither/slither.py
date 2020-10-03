import logging
import os

from crytic_compile import CryticCompile, InvalidCompilation

# pylint: disable= no-name-in-module
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.printers.abstract_printer import AbstractPrinter
from slither.core.slither_core import SlitherCore
from slither.exceptions import SlitherError
from slither.solc_parsing.slitherSolc import SlitherSolc

logger = logging.getLogger("Slither")
logging.basicConfig()

logger_detector = logging.getLogger("Detectors")
logger_printer = logging.getLogger("Printers")


def _check_common_things(thing_name, cls, base_cls, instances_list):

    if not issubclass(cls, base_cls) or cls is base_cls:
        raise Exception(
            "You can't register {!r} as a {}. You need to pass a class that inherits from {}".format(
                cls, thing_name, base_cls.__name__
            )
        )

    if any(type(obj) == cls for obj in instances_list):  # pylint: disable=unidiomatic-typecheck
        raise Exception("You can't register {!r} twice.".format(cls))


class Slither(SlitherCore):  # pylint: disable=too-many-instance-attributes
    def __init__(self, target, **kwargs):
        """
        Args:
            target (str | list(json) | CryticCompile)
        Keyword Args:
            solc (str): solc binary location (default 'solc')
            disable_solc_warnings (bool): True to disable solc warnings (default false)
            solc_arguments (str): solc arguments (default '')
            ast_format (str): ast format (default '--ast-compact-json')
            filter_paths (list(str)): list of path to filter (default [])
            triage_mode (bool): if true, switch to triage mode (default false)
            exclude_dependencies (bool): if true, exclude results that are only related to dependencies
            generate_patches (bool): if true, patches are generated (json output only)

            truffle_ignore (bool): ignore truffle.js presence (default false)
            truffle_build_directory (str): build truffle directory (default 'build/contracts')
            truffle_ignore_compile (bool): do not run truffle compile (default False)
            truffle_version (str): use a specific truffle version (default None)

            embark_ignore (bool): ignore embark.js presence (default false)
            embark_ignore_compile (bool): do not run embark build (default False)
            embark_overwrite_config (bool): overwrite original config file (default false)

        """
        super().__init__()
        self._parser: SlitherSolc  #  This could be another parser, like SlitherVyper, interface needs to be determined

        self._disallow_partial: bool = kwargs.get("disallow_partial", False)
        self._skip_assembly: bool = kwargs.get("skip_assembly", False)

        # list of files provided (see --splitted option)
        if isinstance(target, list):
            self._init_from_list(target)
        elif isinstance(target, str) and target.endswith(".json"):
            self._init_from_raw_json(target)
        else:
            self._parser = SlitherSolc("", self)
            try:
                if isinstance(target, CryticCompile):
                    crytic_compile = target
                else:
                    crytic_compile = CryticCompile(target, **kwargs)
                self._crytic_compile = crytic_compile
            except InvalidCompilation as e:
                # pylint: disable=raise-missing-from
                raise SlitherError(f"Invalid compilation: \n{str(e)}")
            for path, ast in crytic_compile.asts.items():
                self._parser.parse_contracts_from_loaded_json(ast, path)
                self.add_source_code(path)

        if kwargs.get("generate_patches", False):
            self.generate_patches = True

        self._markdown_root = kwargs.get("markdown_root", "")

        self._detectors = []
        self._printers = []

        filter_paths = kwargs.get("filter_paths", [])
        for p in filter_paths:
            self.add_path_to_filter(p)

        self._exclude_dependencies = kwargs.get("exclude_dependencies", False)

        triage_mode = kwargs.get("triage_mode", False)
        self._triage_mode = triage_mode

        self._parser.parse_contracts()

        # skip_analyze is only used for testing
        if not kwargs.get("skip_analyze", False):
            self._parser.analyze_contracts()

    def _init_from_raw_json(self, filename):
        if not os.path.isfile(filename):
            raise SlitherError(
                "{} does not exist (are you in the correct directory?)".format(filename)
            )
        assert filename.endswith("json")
        with open(filename, encoding="utf8") as astFile:
            stdout = astFile.read()
            if not stdout:
                to_log = f"Empty AST file: {filename}"
                raise SlitherError(to_log)
        contracts_json = stdout.split("\n=")

        self._parser = SlitherSolc(filename, self)

        for c in contracts_json:
            self._parser.parse_contracts_from_json(c)

    def _init_from_list(self, contract):
        self._parser = SlitherSolc("", self)
        for c in contract:
            if "absolutePath" in c:
                path = c["absolutePath"]
            else:
                path = c["attributes"]["absolutePath"]
            self._parser.parse_contracts_from_loaded_json(c, path)

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

    @property
    def detectors_optimization(self):
        return [d for d in self.detectors if d.IMPACT == DetectorClassification.OPTIMIZATION]

    def register_detector(self, detector_class):
        """
        :param detector_class: Class inheriting from `AbstractDetector`.
        """
        _check_common_things("detector", detector_class, AbstractDetector, self._detectors)

        instance = detector_class(self, logger_detector)
        self._detectors.append(instance)

    def register_printer(self, printer_class):
        """
        :param printer_class: Class inheriting from `AbstractPrinter`.
        """
        _check_common_things("printer", printer_class, AbstractPrinter, self._printers)

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

        return [p.output(self.filename).data for p in self._printers]

    @property
    def triage_mode(self):
        return self._triage_mode
