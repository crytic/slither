import logging
from typing import Union, List, ValuesView, Type, Dict, Optional

from crytic_compile import CryticCompile, InvalidCompilation

# pylint: disable= no-name-in-module
from slither.core.compilation_unit import SlitherCompilationUnit
from slither.core.scope.scope import FileScope
from slither.core.slither_core import SlitherCore
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.exceptions import SlitherError
from slither.printers.abstract_printer import AbstractPrinter
from slither.solc_parsing.slither_compilation_unit_solc import SlitherCompilationUnitSolc
from slither.vyper_parsing.vyper_compilation_unit import VyperCompilationUnit
from slither.utils.output import Output
from slither.vyper_parsing.ast.ast import parse

logger = logging.getLogger("Slither")
logging.basicConfig()

logger_detector = logging.getLogger("Detectors")
logger_printer = logging.getLogger("Printers")


def _check_common_things(
    thing_name: str, cls: Type, base_cls: Type, instances_list: List[Type[AbstractDetector]]
) -> None:

    if not issubclass(cls, base_cls) or cls is base_cls:
        raise Exception(
            f"You can't register {cls!r} as a {thing_name}. You need to pass a class that inherits from {base_cls.__name__}"
        )

    if any(type(obj) == cls for obj in instances_list):  # pylint: disable=unidiomatic-typecheck
        raise Exception(f"You can't register {cls!r} twice.")


def _update_file_scopes(candidates: ValuesView[FileScope]):
    """
    Because solc's import allows cycle in the import
    We iterate until we aren't adding new information to the scope

    """
    learned_something = False
    while True:
        for candidate in candidates:
            learned_something |= candidate.add_accesible_scopes()
        if not learned_something:
            break
        learned_something = False


class Slither(
    SlitherCore
):  # pylint: disable=too-many-instance-attributes,too-many-locals,too-many-statements
    def __init__(self, target: Union[str, CryticCompile], **kwargs) -> None:
        """
        Args:
            target (str | CryticCompile)
        Keyword Args:
            solc (str): solc binary location (default 'solc')
            disable_solc_warnings (bool): True to disable solc warnings (default false)
            solc_args (str): solc arguments (default '')
            ast_format (str): ast format (default '--ast-compact-json')
            filter_paths (list(str)): list of path to filter (default [])
            triage_mode (bool): if true, switch to triage mode (default false)
            exclude_dependencies (bool): if true, exclude results that are only related to dependencies
            generate_patches (bool): if true, patches are generated (json output only)
            change_line_prefix (str): Change the line prefix (default #)
                for the displayed source codes (i.e. file.sol#1).

        """
        super().__init__()

        self._disallow_partial: bool = kwargs.get("disallow_partial", False)
        self._skip_assembly: bool = kwargs.get("skip_assembly", False)
        self._show_ignored_findings: bool = kwargs.get("show_ignored_findings", False)

        self.line_prefix = kwargs.get("change_line_prefix", "#")

        # Indicate if Codex related features should be used
        self.codex_enabled = kwargs.get("codex", False)
        self.codex_contracts = kwargs.get("codex_contracts", "all")
        self.codex_model = kwargs.get("codex_model", "text-davinci-003")
        self.codex_temperature = kwargs.get("codex_temperature", 0)
        self.codex_max_tokens = kwargs.get("codex_max_tokens", 300)
        self.codex_log = kwargs.get("codex_log", False)
        self.codex_organization: Optional[str] = kwargs.get("codex_organization", None)

        self.no_fail = kwargs.get("no_fail", False)

        self._parsers: List[SlitherCompilationUnitSolc] = []
        try:
            if isinstance(target, CryticCompile):
                crytic_compile = target
            else:
                crytic_compile = CryticCompile(target, **kwargs)
            self._crytic_compile = crytic_compile
        except InvalidCompilation as e:
            # pylint: disable=raise-missing-from
            raise SlitherError(f"Invalid compilation: \n{str(e)}")
        for compilation_unit in crytic_compile.compilation_units.values():
            compilation_unit_slither = SlitherCompilationUnit(self, compilation_unit)
            self._compilation_units.append(compilation_unit_slither)

            if compilation_unit_slither.is_vyper:
                vyper_parser = VyperCompilationUnit(compilation_unit_slither)
                for path, ast in compilation_unit.asts.items():
                    ast_nodes = parse(ast["ast"])
                    vyper_parser.parse_module(ast_nodes, path)
                self._parsers.append(vyper_parser)
            else:
                # Solidity specific
                assert compilation_unit_slither.is_solidity
                sol_parser = SlitherCompilationUnitSolc(compilation_unit_slither)
                self._parsers.append(sol_parser)
                for path, ast in compilation_unit.asts.items():
                    sol_parser.parse_top_level_items(ast, path)
                    self.add_source_code(path)

                _update_file_scopes(compilation_unit_slither.scopes.values())

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

        printers_to_run = kwargs.get("printers_to_run", "")
        if printers_to_run == "echidna":
            self.skip_data_dependency = True

        self._init_parsing_and_analyses(kwargs.get("skip_analyze", False))

    def _init_parsing_and_analyses(self, skip_analyze: bool) -> None:

        for parser in self._parsers:
            try:
                parser.parse_contracts()
            except Exception as e:
                if self.no_fail:
                    continue
                raise e

        # skip_analyze is only used for testing
        if not skip_analyze:
            for parser in self._parsers:
                try:
                    parser.analyze_contracts()
                except Exception as e:
                    if self.no_fail:
                        continue
                    raise e

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

    def register_detector(self, detector_class: Type[AbstractDetector]) -> None:
        """
        :param detector_class: Class inheriting from `AbstractDetector`.
        """
        _check_common_things("detector", detector_class, AbstractDetector, self._detectors)

        for compilation_unit in self.compilation_units:
            instance = detector_class(compilation_unit, self, logger_detector)
            self._detectors.append(instance)

    def unregister_detector(self, detector_class: Type[AbstractDetector]) -> None:
        """
        :param detector_class: Class inheriting from `AbstractDetector`.
        """

        for obj in self._detectors:
            if isinstance(obj, detector_class):
                self._detectors.remove(obj)
                return

    def register_printer(self, printer_class: Type[AbstractPrinter]) -> None:
        """
        :param printer_class: Class inheriting from `AbstractPrinter`.
        """
        _check_common_things("printer", printer_class, AbstractPrinter, self._printers)

        instance = printer_class(self, logger_printer)
        self._printers.append(instance)

    def unregister_printer(self, printer_class: Type[AbstractPrinter]) -> None:
        """
        :param printer_class: Class inheriting from `AbstractPrinter`.
        """

        for obj in self._printers:
            if isinstance(obj, printer_class):
                self._printers.remove(obj)
                return

    def run_detectors(self) -> List[Dict]:
        """
        :return: List of registered detectors results.
        """

        self.load_previous_results()
        results = [d.detect() for d in self._detectors]

        self.write_results_to_hide()
        return results

    def run_printers(self) -> List[Output]:
        """
        :return: List of registered printers outputs.
        """

        return [p.output(self._crytic_compile.target).data for p in self._printers]

    @property
    def triage_mode(self) -> bool:
        return self._triage_mode
