"""
    Main module
"""
import json
import logging
import os
import pathlib
import posixpath
import re
from collections import defaultdict
from typing import Optional, Dict, List, Set, Union, Tuple

from crytic_compile import CryticCompile
from crytic_compile.utils.naming import Filename

from slither.core.declarations.contract_level import ContractLevel
from slither.core.compilation_unit import SlitherCompilationUnit
from slither.core.context.context import Context
from slither.core.declarations import Contract, FunctionContract
from slither.core.declarations.top_level import TopLevel
from slither.core.source_mapping.source_mapping import SourceMapping, Source
from slither.slithir.variables import Constant
from slither.utils.colors import red
from slither.utils.sarif import read_triage_info
from slither.utils.source_mapping import get_definition, get_references, get_implementation

logger = logging.getLogger("Slither")
logging.basicConfig()


def _relative_path_format(path: str) -> str:
    """
    Strip relative paths of "." and ".."
    """
    return path.split("..")[-1].strip(".").strip("/")


# pylint: disable=too-many-instance-attributes,too-many-public-methods
class SlitherCore(Context):
    """
    Slither static analyzer
    """

    def __init__(self) -> None:
        super().__init__()

        self._filename: Optional[str] = None
        self._raw_source_code: Dict[str, str] = {}
        self._source_code_to_line: Optional[Dict[str, List[str]]] = None

        self._previous_results_filename: str = "slither.db.json"

        # TODO: add cli flag to set these variables
        self.sarif_input: str = "export.sarif"
        self.sarif_triage: str = "export.sarif.sarifexplorer"
        self._results_to_hide: List = []
        self._previous_results: List = []
        # From triaged result
        self._previous_results_ids: Set[str] = set()
        # Every slither object has a list of result from detector
        # Because of the multiple compilation support, we might analyze
        # Multiple time the same result, so we remove duplicates
        self._currently_seen_resuts: Set[str] = set()
        self._paths_to_filter: Set[str] = set()

        self._crytic_compile: Optional[CryticCompile] = None

        self._generate_patches = False
        self._exclude_dependencies = False

        self._markdown_root = ""

        # If set to true, slither will not catch errors during parsing
        self._disallow_partial: bool = False
        self._skip_assembly: bool = False

        self._show_ignored_findings = False

        # Maps from file to detector name to the start/end ranges for that detector.
        # Infinity is used to signal a detector has no end range.
        self._ignore_ranges: Dict[str, Dict[str, List[Tuple[int, ...]]]] = defaultdict(
            lambda: defaultdict(lambda: [(-1, -1)])
        )

        self._compilation_units: List[SlitherCompilationUnit] = []

        self._contracts: List[Contract] = []
        self._contracts_derived: List[Contract] = []

        self._offset_to_objects: Optional[Dict[Filename, Dict[int, Set[SourceMapping]]]] = None
        self._offset_to_references: Optional[Dict[Filename, Dict[int, Set[Source]]]] = None
        self._offset_to_implementations: Optional[Dict[Filename, Dict[int, Set[Source]]]] = None
        self._offset_to_definitions: Optional[Dict[Filename, Dict[int, Set[Source]]]] = None

        # Line prefix is used during the source mapping generation
        # By default we generate file.sol#1
        # But we allow to alter this (ex: file.sol:1) for vscode integration
        self.line_prefix: str = "#"

        # Use by the echidna printer
        # If true, partial analysis is allowed
        self.no_fail = False

        self.skip_data_dependency = False

    @property
    def compilation_units(self) -> List[SlitherCompilationUnit]:
        return list(self._compilation_units)

    def add_compilation_unit(self, compilation_unit: SlitherCompilationUnit):
        self._compilation_units.append(compilation_unit)

    # endregion
    ###################################################################################
    ###################################################################################
    # region Contracts
    ###################################################################################
    ###################################################################################

    @property
    def contracts(self) -> List[Contract]:
        if not self._contracts:
            all_contracts = [
                compilation_unit.contracts for compilation_unit in self._compilation_units
            ]
            self._contracts = [item for sublist in all_contracts for item in sublist]
        return self._contracts

    @property
    def contracts_derived(self) -> List[Contract]:
        if not self._contracts_derived:
            all_contracts = [
                compilation_unit.contracts_derived for compilation_unit in self._compilation_units
            ]
            self._contracts_derived = [item for sublist in all_contracts for item in sublist]
        return self._contracts_derived

    def get_contract_from_name(self, contract_name: Union[str, Constant]) -> List[Contract]:
        """
            Return a contract from a name
        Args:
            contract_name (str): name of the contract
        Returns:
            Contract
        """
        contracts = []
        for compilation_unit in self._compilation_units:
            contracts += compilation_unit.get_contract_from_name(contract_name)
        return contracts

    ###################################################################################
    ###################################################################################
    # region Source code
    ###################################################################################
    ###################################################################################

    @property
    def source_code(self) -> Dict[str, str]:
        """{filename: source_code (str)}: source code"""
        return self._raw_source_code

    @property
    def filename(self) -> Optional[str]:
        """str: Filename."""
        return self._filename

    @filename.setter
    def filename(self, filename: str):
        self._filename = filename

    def add_source_code(self, path: str) -> None:
        """
        :param path:
        :return:
        """
        if self.crytic_compile and path in self.crytic_compile.src_content:
            self.source_code[path] = self.crytic_compile.src_content[path]
        else:
            with open(path, encoding="utf8", newline="") as f:
                self.source_code[path] = f.read()

        self.parse_ignore_comments(path)

    @property
    def markdown_root(self) -> str:
        return self._markdown_root

    def print_functions(self, d: str):
        """
        Export all the functions to dot files
        """
        for compilation_unit in self._compilation_units:
            for c in compilation_unit.contracts:
                for f in c.functions:
                    f.cfg_to_dot(os.path.join(d, f"{c.name}.{f.name}.dot"))

    def offset_to_objects(self, filename_str: str, offset: int) -> Set[SourceMapping]:
        if self._offset_to_objects is None:
            self._compute_offsets_to_ref_impl_decl()
        filename: Filename = self.crytic_compile.filename_lookup(filename_str)
        return self._offset_to_objects[filename][offset]

    def _compute_offsets_from_thing(self, thing: SourceMapping):
        definition = get_definition(thing, self.crytic_compile)
        references = get_references(thing)
        implementation = get_implementation(thing)

        for offset in range(definition.start, definition.end + 1):

            if (
                isinstance(thing, TopLevel)
                or (
                    isinstance(thing, FunctionContract)
                    and thing.contract_declarer == thing.contract
                )
                or (isinstance(thing, ContractLevel) and not isinstance(thing, FunctionContract))
            ):
                self._offset_to_objects[definition.filename][offset].add(thing)

            self._offset_to_definitions[definition.filename][offset].add(definition)
            self._offset_to_implementations[definition.filename][offset].add(implementation)
            self._offset_to_references[definition.filename][offset] |= set(references)

        for ref in references:
            for offset in range(ref.start, ref.end + 1):

                if (
                    isinstance(thing, TopLevel)
                    or (
                        isinstance(thing, FunctionContract)
                        and thing.contract_declarer == thing.contract
                    )
                    or (
                        isinstance(thing, ContractLevel) and not isinstance(thing, FunctionContract)
                    )
                ):
                    self._offset_to_objects[definition.filename][offset].add(thing)

                self._offset_to_definitions[ref.filename][offset].add(definition)
                self._offset_to_implementations[ref.filename][offset].add(implementation)
                self._offset_to_references[ref.filename][offset] |= set(references)

    def _compute_offsets_to_ref_impl_decl(self):  # pylint: disable=too-many-branches
        self._offset_to_references = defaultdict(lambda: defaultdict(lambda: set()))
        self._offset_to_definitions = defaultdict(lambda: defaultdict(lambda: set()))
        self._offset_to_implementations = defaultdict(lambda: defaultdict(lambda: set()))
        self._offset_to_objects = defaultdict(lambda: defaultdict(lambda: set()))

        for compilation_unit in self._compilation_units:
            for contract in compilation_unit.contracts:
                self._compute_offsets_from_thing(contract)

                for function in contract.functions:
                    self._compute_offsets_from_thing(function)
                    for variable in function.local_variables:
                        self._compute_offsets_from_thing(variable)
                for modifier in contract.modifiers:
                    self._compute_offsets_from_thing(modifier)
                    for variable in modifier.local_variables:
                        self._compute_offsets_from_thing(variable)

                for st in contract.structures:
                    self._compute_offsets_from_thing(st)

                for enum in contract.enums:
                    self._compute_offsets_from_thing(enum)

                for event in contract.events:
                    self._compute_offsets_from_thing(event)
            for enum in compilation_unit.enums_top_level:
                self._compute_offsets_from_thing(enum)
            for function in compilation_unit.functions_top_level:
                self._compute_offsets_from_thing(function)
            for st in compilation_unit.structures_top_level:
                self._compute_offsets_from_thing(st)
            for import_directive in compilation_unit.import_directives:
                self._compute_offsets_from_thing(import_directive)
            for pragma in compilation_unit.pragma_directives:
                self._compute_offsets_from_thing(pragma)

    def offset_to_references(self, filename_str: str, offset: int) -> Set[Source]:
        if self._offset_to_references is None:
            self._compute_offsets_to_ref_impl_decl()
        filename: Filename = self.crytic_compile.filename_lookup(filename_str)
        return self._offset_to_references[filename][offset]

    def offset_to_implementations(self, filename_str: str, offset: int) -> Set[Source]:
        if self._offset_to_implementations is None:
            self._compute_offsets_to_ref_impl_decl()
        filename: Filename = self.crytic_compile.filename_lookup(filename_str)
        return self._offset_to_implementations[filename][offset]

    def offset_to_definitions(self, filename_str: str, offset: int) -> Set[Source]:
        if self._offset_to_definitions is None:
            self._compute_offsets_to_ref_impl_decl()
        filename: Filename = self.crytic_compile.filename_lookup(filename_str)
        return self._offset_to_definitions[filename][offset]

    # endregion
    ###################################################################################
    ###################################################################################
    # region Filtering results
    ###################################################################################
    ###################################################################################

    def parse_ignore_comments(self, file: str) -> None:
        # The first time we check a file, find all start/end ignore comments and memoize them.
        line_number = 1
        while True:

            line_text = self.crytic_compile.get_code_from_line(file, line_number)
            if line_text is None:
                break

            start_regex = r"^\s*//\s*slither-disable-start\s*([a-zA-Z0-9_,-]*)"
            end_regex = r"^\s*//\s*slither-disable-end\s*([a-zA-Z0-9_,-]*)"
            start_match = re.findall(start_regex, line_text.decode("utf8"))
            end_match = re.findall(end_regex, line_text.decode("utf8"))

            if start_match:
                ignored = start_match[0].split(",")
                if ignored:
                    for check in ignored:
                        vals = self._ignore_ranges[file][check]
                        if len(vals) == 0 or vals[-1][1] != float("inf"):
                            # First item in the array, or the prior item is fully populated.
                            self._ignore_ranges[file][check].append((line_number, float("inf")))
                        else:
                            logger.error(
                                f"Consecutive slither-disable-starts without slither-disable-end in {file}#{line_number}"
                            )
                            return

            if end_match:
                ignored = end_match[0].split(",")
                if ignored:
                    for check in ignored:
                        vals = self._ignore_ranges[file][check]
                        if len(vals) == 0 or vals[-1][1] != float("inf"):
                            logger.error(
                                f"slither-disable-end without slither-disable-start in {file}#{line_number}"
                            )
                            return
                        self._ignore_ranges[file][check][-1] = (vals[-1][0], line_number)

            line_number += 1

    def has_ignore_comment(self, r: Dict) -> bool:
        """
        Check if the result has an ignore comment in the file or on the preceding line, in which
        case, it is not valid
        """
        if not self.crytic_compile:
            return False
        mapping_elements_with_lines = (
            (
                posixpath.normpath(elem["source_mapping"]["filename_absolute"]),
                elem["source_mapping"]["lines"],
            )
            for elem in r["elements"]
            if "source_mapping" in elem
            and "filename_absolute" in elem["source_mapping"]
            and "lines" in elem["source_mapping"]
            and len(elem["source_mapping"]["lines"]) > 0
        )

        for file, lines in mapping_elements_with_lines:

            # Check if result is within an ignored range.
            ignore_ranges = self._ignore_ranges[file][r["check"]] + self._ignore_ranges[file]["all"]
            for start, end in ignore_ranges:
                # The full check must be within the ignore range to be ignored.
                if start < lines[0] and end > lines[-1]:
                    return True

            # Check for next-line matchers.
            ignore_line_index = min(lines) - 1
            ignore_line_text = self.crytic_compile.get_code_from_line(file, ignore_line_index)
            if ignore_line_text:
                match = re.findall(
                    r"^\s*//\s*slither-disable-next-line\s*([a-zA-Z0-9_,-]*)",
                    ignore_line_text.decode("utf8"),
                )
                if match:
                    ignored = match[0].split(",")
                    if ignored and ("all" in ignored or any(r["check"] == c for c in ignored)):
                        return True

        return False

    def valid_result(self, r: Dict) -> bool:
        """
        Check if the result is valid
        A result is invalid if:
            - All its source paths belong to the source path filtered
            - Or a similar result was reported and saved during a previous run
            - The --exclude-dependencies flag is set and results are only related to dependencies
            - There is an ignore comment on the preceding line or in the file
        """

        # Remove duplicate due to the multiple compilation support
        if r["id"] in self._currently_seen_resuts:
            return False
        self._currently_seen_resuts.add(r["id"])

        source_mapping_elements = [
            elem["source_mapping"].get("filename_absolute", "unknown")
            for elem in r["elements"]
            if "source_mapping" in elem
        ]

        # Use POSIX-style paths so that filter_paths works across different
        # OSes. Convert to a list so elements don't get consumed and are lost
        # while evaluating the first pattern
        source_mapping_elements = list(
            map(lambda x: pathlib.Path(x).resolve().as_posix() if x else x, source_mapping_elements)
        )
        matching = False

        for path in self._paths_to_filter:
            try:
                if any(
                    bool(re.search(_relative_path_format(path), src_mapping))
                    for src_mapping in source_mapping_elements
                ):
                    matching = True
                    break
            except re.error:
                logger.error(
                    f"Incorrect regular expression for --filter-paths {path}."
                    "\nSlither supports the Python re format"
                    ": https://docs.python.org/3/library/re.html"
                )

        if r["elements"] and matching:
            return False

        if self._show_ignored_findings:
            return True
        if self.has_ignore_comment(r):
            return False
        if r["id"] in self._previous_results_ids:
            return False
        if r["elements"] and self._exclude_dependencies:
            if all(element["source_mapping"]["is_dependency"] for element in r["elements"]):
                return False
        # Conserve previous result filtering. This is conserved for compatibility, but is meant to be removed
        if r["description"] in [pr["description"] for pr in self._previous_results]:
            return False

        return True

    def load_previous_results(self) -> None:
        self.load_previous_results_from_sarif()

        filename = self._previous_results_filename
        try:
            if os.path.isfile(filename):
                with open(filename, encoding="utf8") as f:
                    self._previous_results = json.load(f)
                    if self._previous_results:
                        for r in self._previous_results:
                            if "id" in r:
                                self._previous_results_ids.add(r["id"])

        except json.decoder.JSONDecodeError:
            logger.error(red(f"Impossible to decode {filename}. Consider removing the file"))

    def load_previous_results_from_sarif(self) -> None:
        sarif = pathlib.Path(self.sarif_input)
        triage = pathlib.Path(self.sarif_triage)

        if not sarif.exists():
            return
        if not triage.exists():
            return

        triaged = read_triage_info(sarif, triage)

        for id_triaged in triaged:
            self._previous_results_ids.add(id_triaged)

    def write_results_to_hide(self) -> None:
        if not self._results_to_hide:
            return
        filename = self._previous_results_filename
        with open(filename, "w", encoding="utf8") as f:
            results = self._results_to_hide + self._previous_results
            json.dump(results, f)

    def save_results_to_hide(self, results: List[Dict]) -> None:
        self._results_to_hide += results

    def add_path_to_filter(self, path: str):
        """
        Add path to filter
        Path are used through direct comparison (no regex)
        """
        self._paths_to_filter.add(path)

    # endregion
    ###################################################################################
    ###################################################################################
    # region Crytic compile
    ###################################################################################
    ###################################################################################

    @property
    def crytic_compile(self) -> CryticCompile:
        return self._crytic_compile  # type: ignore

    # endregion
    ###################################################################################
    ###################################################################################
    # region Format
    ###################################################################################
    ###################################################################################

    @property
    def generate_patches(self) -> bool:
        return self._generate_patches

    @generate_patches.setter
    def generate_patches(self, p: bool):
        self._generate_patches = p

    # endregion
    ###################################################################################
    ###################################################################################
    # region Internals
    ###################################################################################
    ###################################################################################

    @property
    def disallow_partial(self) -> bool:
        """
        Return true if partial analyses are disallowed
        For example, codebase with duplicate names will lead to partial analyses

        :return:
        """
        return self._disallow_partial

    @property
    def skip_assembly(self) -> bool:
        return self._skip_assembly

    @property
    def show_ignore_findings(self) -> bool:
        return self._show_ignored_findings

    # endregion
