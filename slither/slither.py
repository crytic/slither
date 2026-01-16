import logging

from crytic_compile import CryticCompile, InvalidCompilation


from slither.core.compilation_unit import SlitherCompilationUnit
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
    thing_name: str, cls: type, base_cls: type, instances_list: list[type[AbstractDetector]]
) -> None:
    if not issubclass(cls, base_cls) or cls is base_cls:
        raise SlitherError(
            f"You can't register {cls!r} as a {thing_name}. You need to pass a class that inherits from {base_cls.__name__}"
        )

    if any(type(obj) is cls for obj in instances_list):
        raise SlitherError(f"You can't register {cls!r} twice.")


def _update_file_scopes(
    sol_parser: SlitherCompilationUnitSolc,
):
    """
    Since all definitions in a file are exported by default, including definitions from its (transitive) dependencies,
    we can identify all top level items that could possibly be referenced within the file from its exportedSymbols.
    It is not as straightforward for user defined types and functions as well as aliasing. See add_accessible_scopes for more details.
    """
    candidates = sol_parser.compilation_unit.scopes.values()
    learned_something = False
    # Because solc's import allows cycle in the import graph, iterate until we aren't adding new information to the scope.
    while True:
        for candidate in candidates:
            learned_something |= candidate.add_accessible_scopes()
        if not learned_something:
            break
        learned_something = False

    for scope in candidates:
        for refId in scope.exported_symbols:
            if refId in sol_parser.contracts_by_id:
                contract = sol_parser.contracts_by_id[refId]
                scope.contracts[contract.name] = contract
            elif refId in sol_parser.functions_by_id:
                functions = sol_parser.functions_by_id[refId]
                assert len(functions) == 1
                scope.functions.add(functions[0])
            elif refId in sol_parser.imports_by_id:
                import_directive = sol_parser.imports_by_id[refId]
                scope.imports.add(import_directive)
            elif refId in sol_parser.top_level_variables_by_id:
                top_level_variable = sol_parser.top_level_variables_by_id[refId]
                scope.variables[top_level_variable.name] = top_level_variable
            elif refId in sol_parser.top_level_events_by_id:
                top_level_event = sol_parser.top_level_events_by_id[refId]
                scope.events.add(top_level_event)
            elif refId in sol_parser.top_level_structures_by_id:
                top_level_struct = sol_parser.top_level_structures_by_id[refId]
                scope.structures[top_level_struct.name] = top_level_struct
            elif refId in sol_parser.top_level_type_aliases_by_id:
                top_level_type_alias = sol_parser.top_level_type_aliases_by_id[refId]
                scope.type_aliases[top_level_type_alias.name] = top_level_type_alias
            elif refId in sol_parser.top_level_enums_by_id:
                top_level_enum = sol_parser.top_level_enums_by_id[refId]
                scope.enums[top_level_enum.name] = top_level_enum
            elif refId in sol_parser.top_level_errors_by_id:
                top_level_custom_error = sol_parser.top_level_errors_by_id[refId]
                scope.custom_errors.add(top_level_custom_error)
            else:
                logger.error(
                    f"Failed to resolved name for reference id {refId} in {scope.filename.absolute}."
                )


class Slither(SlitherCore):
    def __init__(self, target: str | CryticCompile, **kwargs) -> None:
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
        self.codex_organization: str | None = kwargs.get("codex_organization")

        self.no_fail = kwargs.get("no_fail", False)

        self._parsers: list[SlitherCompilationUnitSolc] = []
        try:
            if isinstance(target, CryticCompile):
                crytic_compile = target
            else:
                crytic_compile = CryticCompile(target, **kwargs)
            self._crytic_compile = crytic_compile
        except InvalidCompilation as e:
            raise SlitherError(f"Invalid compilation: \n{e!s}")
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

                for contract in sol_parser._underlying_contract_to_parser:
                    if contract.name.startswith("SlitherInternalTopLevelContract"):
                        raise SlitherError(
                            # region multi-line-string
                            """Your codebase has a contract named 'SlitherInternalTopLevelContract'.
        Please rename it, this name is reserved for Slither's internals"""
                            # endregion multi-line
                        )
                    sol_parser._contracts_by_id[contract.id] = contract
                    sol_parser._compilation_unit.contracts.append(contract)

                _update_file_scopes(sol_parser)

        if kwargs.get("generate_patches", False):
            self.generate_patches = True

        self._markdown_root = kwargs.get("markdown_root", "")

        self._detectors = []
        self._printers = []

        filter_paths = kwargs.get("filter_paths", [])
        for p in filter_paths:
            self.add_path_to_filter(p)

        include_paths = kwargs.get("include_paths", [])
        for p in include_paths:
            self.add_path_to_include(p)

        self._exclude_dependencies = kwargs.get("exclude_dependencies", False)

        triage_mode = kwargs.get("triage_mode", False)
        triage_database = kwargs.get("triage_database", "slither.db.json")
        self._triage_mode = triage_mode
        self._previous_results_filename = triage_database

        printers_to_run = kwargs.get("printers_to_run", "")
        if printers_to_run == "echidna":
            self.skip_data_dependency = True

        # Used in inheritance-graph printer
        self.include_interfaces = kwargs.get("include_interfaces", False)

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

    def register_detector(self, detector_class: type[AbstractDetector]) -> None:
        """
        :param detector_class: Class inheriting from `AbstractDetector`.
        """
        _check_common_things("detector", detector_class, AbstractDetector, self._detectors)

        for compilation_unit in self.compilation_units:
            instance = detector_class(compilation_unit, self, logger_detector)
            self._detectors.append(instance)

    def unregister_detector(self, detector_class: type[AbstractDetector]) -> None:
        """
        :param detector_class: Class inheriting from `AbstractDetector`.
        """

        for obj in self._detectors:
            if isinstance(obj, detector_class):
                self._detectors.remove(obj)
                return

    def register_printer(self, printer_class: type[AbstractPrinter]) -> None:
        """
        :param printer_class: Class inheriting from `AbstractPrinter`.
        """
        _check_common_things("printer", printer_class, AbstractPrinter, self._printers)

        instance = printer_class(self, logger_printer)
        self._printers.append(instance)

    def unregister_printer(self, printer_class: type[AbstractPrinter]) -> None:
        """
        :param printer_class: Class inheriting from `AbstractPrinter`.
        """

        for obj in self._printers:
            if isinstance(obj, printer_class):
                self._printers.remove(obj)
                return

    def run_detectors(self) -> list[dict]:
        """
        :return: List of registered detectors results.
        """

        self.load_previous_results()
        results = [d.detect() for d in self._detectors]

        self.write_results_to_hide()
        return results

    def run_printers(self) -> list[Output]:
        """
        :return: List of registered printers outputs.
        """

        return [p.output(self._crytic_compile.target).data for p in self._printers]

    @property
    def triage_mode(self) -> bool:
        return self._triage_mode
