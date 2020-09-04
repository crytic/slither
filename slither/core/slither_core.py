"""
    Main module
"""
import os
import logging
import json
import re
import math
from collections import defaultdict
from typing import Optional, Dict, List, Set, Union, Tuple

from crytic_compile import CryticCompile

from slither.core.context.context import Context
from slither.core.declarations import (
    Contract,
    Pragma,
    Import,
    Function,
    Modifier,
    Structure,
    Enum,
)
from slither.core.variables.state_variable import StateVariable
from slither.slithir.operations import InternalCall
from slither.slithir.variables import Constant
from slither.utils.colors import red

logger = logging.getLogger("Slither")
logging.basicConfig()


def _relative_path_format(path: str) -> str:
    """
    Strip relative paths of "." and ".."
    """
    return path.split("..")[-1].strip(".").strip("/")


class SlitherCore(Context):  # pylint: disable=too-many-instance-attributes,too-many-public-methods
    """
    Slither static analyzer
    """

    def __init__(self):
        super().__init__()
        self._contracts: Dict[str, Contract] = {}
        self._filename: Optional[str] = None
        self._source_units: Dict[int, str] = {}
        self._solc_version: Optional[str] = None  # '0.3' or '0.4':!
        self._pragma_directives: List[Pragma] = []
        self._import_directives: List[Import] = []
        self._raw_source_code: Dict[str, str] = {}
        self._all_functions: Set[Function] = set()
        self._all_modifiers: Set[Modifier] = set()
        # Memoize
        self._all_state_variables: Optional[Set[StateVariable]] = None

        self._previous_results_filename: str = "slither.db.json"
        self._results_to_hide: List = []
        self._previous_results: List = []
        self._previous_results_ids: Set[str] = set()
        self._paths_to_filter: Set[str] = set()

        self._crytic_compile: Optional[CryticCompile] = None

        self._generate_patches = False
        self._exclude_dependencies = False

        self._markdown_root = ""

        self._contract_name_collisions = defaultdict(list)
        self._contract_with_missing_inheritance = set()

        self._storage_layouts: Dict[str, Dict[str, Tuple[int, int]]] = {}

        # If set to true, slither will not catch errors during parsing
        self._disallow_partial: bool = False

    ###################################################################################
    ###################################################################################
    # region Source code
    ###################################################################################
    ###################################################################################

    @property
    def source_code(self) -> Dict[str, str]:
        """ {filename: source_code (str)}: source code """
        return self._raw_source_code

    @property
    def source_units(self) -> Dict[int, str]:
        return self._source_units

    @property
    def filename(self) -> Optional[str]:
        """str: Filename."""
        return self._filename

    @filename.setter
    def filename(self, filename: str):
        self._filename = filename

    def add_source_code(self, path):
        """
        :param path:
        :return:
        """
        if self.crytic_compile and path in self.crytic_compile.src_content:
            self.source_code[path] = self.crytic_compile.src_content[path]
        else:
            with open(path, encoding="utf8", newline="") as f:
                self.source_code[path] = f.read()

    @property
    def markdown_root(self) -> str:
        return self._markdown_root

    # endregion
    ###################################################################################
    ###################################################################################
    # region Pragma attributes
    ###################################################################################
    ###################################################################################

    @property
    def solc_version(self) -> str:
        """str: Solidity version."""
        if self.crytic_compile:
            return self.crytic_compile.compiler_version.version
        return self._solc_version

    @solc_version.setter
    def solc_version(self, version: str):
        self._solc_version = version

    @property
    def pragma_directives(self) -> List[Pragma]:
        """ list(core.declarations.Pragma): Pragma directives."""
        return self._pragma_directives

    @property
    def import_directives(self) -> List[Import]:
        """ list(core.declarations.Import): Import directives"""
        return self._import_directives

    # endregion
    ###################################################################################
    ###################################################################################
    # region Contracts
    ###################################################################################
    ###################################################################################

    @property
    def contracts(self) -> List[Contract]:
        """list(Contract): List of contracts."""
        return list(self._contracts.values())

    @property
    def contracts_derived(self) -> List[Contract]:
        """list(Contract): List of contracts that are derived and not inherited."""
        inheritance = (x.inheritance for x in self.contracts)
        inheritance = [item for sublist in inheritance for item in sublist]
        return [c for c in self._contracts.values() if c not in inheritance and not c.is_top_level]

    @property
    def contracts_as_dict(self) -> Dict[str, Contract]:
        """list(dict(str: Contract): List of contracts as dict: name -> Contract."""
        return self._contracts

    def get_contract_from_name(self, contract_name: Union[str, Constant]) -> Optional[Contract]:
        """
            Return a contract from a name
        Args:
            contract_name (str): name of the contract
        Returns:
            Contract
        """
        return next((c for c in self.contracts if c.name == contract_name), None)

    # endregion
    ###################################################################################
    ###################################################################################
    # region Functions and modifiers
    ###################################################################################
    ###################################################################################

    @property
    def functions(self) -> List[Function]:
        return list(self._all_functions)

    def add_function(self, func: Function):
        self._all_functions.add(func)

    @property
    def modifiers(self) -> List[Modifier]:
        return list(self._all_modifiers)

    def add_modifier(self, modif: Modifier):
        self._all_modifiers.add(modif)

    @property
    def functions_and_modifiers(self) -> List[Function]:
        return self.functions + self.modifiers

    def propagate_function_calls(self):
        for f in self.functions_and_modifiers:
            for node in f.nodes:
                for ir in node.irs_ssa:
                    if isinstance(ir, InternalCall):
                        ir.function.add_reachable_from_node(node, ir)

    # endregion
    ###################################################################################
    ###################################################################################
    # region Variables
    ###################################################################################
    ###################################################################################

    @property
    def state_variables(self) -> List[StateVariable]:
        if self._all_state_variables is None:
            state_variables = [c.state_variables for c in self.contracts]
            state_variables = [item for sublist in state_variables for item in sublist]
            self._all_state_variables = set(state_variables)
        return list(self._all_state_variables)

    # endregion
    ###################################################################################
    ###################################################################################
    # region Top level
    ###################################################################################
    ###################################################################################

    @property
    def top_level_structures(self) -> List[Structure]:
        top_level_structures = [c.structures for c in self.contracts if c.is_top_level]
        return [st for sublist in top_level_structures for st in sublist]

    @property
    def top_level_enums(self) -> List[Enum]:
        top_level_enums = [c.enums for c in self.contracts if c.is_top_level]
        return [st for sublist in top_level_enums for st in sublist]

    # endregion
    ###################################################################################
    ###################################################################################
    # region Export
    ###################################################################################
    ###################################################################################

    def print_functions(self, d: str):
        """
        Export all the functions to dot files
        """
        for c in self.contracts:
            for f in c.functions:
                f.cfg_to_dot(os.path.join(d, "{}.{}.dot".format(c.name, f.name)))

    # endregion
    ###################################################################################
    ###################################################################################
    # region Filtering results
    ###################################################################################
    ###################################################################################

    def valid_result(self, r: Dict) -> bool:
        """
        Check if the result is valid
        A result is invalid if:
            - All its source paths belong to the source path filtered
            - Or a similar result was reported and saved during a previous run
            - The --exclude-dependencies flag is set and results are only related to dependencies
        """
        source_mapping_elements = [
            elem["source_mapping"]["filename_absolute"]
            for elem in r["elements"]
            if "source_mapping" in elem
        ]
        source_mapping_elements = map(
            lambda x: os.path.normpath(x) if x else x, source_mapping_elements
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
        if r["elements"] and self._exclude_dependencies:
            return not all(element["source_mapping"]["is_dependency"] for element in r["elements"])
        if r["id"] in self._previous_results_ids:
            return False
        # Conserve previous result filtering. This is conserved for compatibility, but is meant to be removed
        return not r["description"] in [pr["description"] for pr in self._previous_results]

    def load_previous_results(self):
        filename = self._previous_results_filename
        try:
            if os.path.isfile(filename):
                with open(filename) as f:
                    self._previous_results = json.load(f)
                    if self._previous_results:
                        for r in self._previous_results:
                            if "id" in r:
                                self._previous_results_ids.add(r["id"])
        except json.decoder.JSONDecodeError:
            logger.error(
                red("Impossible to decode {}. Consider removing the file".format(filename))
            )

    def write_results_to_hide(self):
        if not self._results_to_hide:
            return
        filename = self._previous_results_filename
        with open(filename, "w", encoding="utf8") as f:
            results = self._results_to_hide + self._previous_results
            json.dump(results, f)

    def save_results_to_hide(self, results: List[Dict]):
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
    def crytic_compile(self) -> Optional[CryticCompile]:
        return self._crytic_compile

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
    def contract_name_collisions(self) -> Dict:
        return self._contract_name_collisions

    @property
    def contracts_with_missing_inheritance(self) -> Set:
        return self._contract_with_missing_inheritance

    @property
    def disallow_partial(self) -> bool:
        """
        Return true if partial analyses are disallowed
        For example, codebase with duplicate names will lead to partial analyses

        :return:
        """
        return self._disallow_partial

    # endregion
    ###################################################################################
    ###################################################################################
    # region Storage Layouts
    ###################################################################################
    ###################################################################################

    def compute_storage_layout(self):
        for contract in self.contracts_derived:
            self._storage_layouts[contract.name] = {}

            slot = 0
            offset = 0
            for var in contract.state_variables_ordered:
                if var.is_constant:
                    continue

                size, new_slot = var.type.storage_size

                if new_slot:
                    if offset > 0:
                        slot += 1
                        offset = 0
                elif size + offset > 32:
                    slot += 1
                    offset = 0

                self._storage_layouts[contract.name][var.canonical_name] = (
                    slot,
                    offset,
                )
                if new_slot:
                    slot += math.ceil(size / 32)
                else:
                    offset += size

    def storage_layout_of(self, contract, var) -> Tuple[int, int]:
        return self._storage_layouts[contract.name][var.canonical_name]

    # endregion
