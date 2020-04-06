"""
    Main module
"""
import os
import logging
import json
import re
from collections import defaultdict

from slither.core.context.context import Context
from slither.slithir.operations import InternalCall
from slither.utils.colors import red

logger = logging.getLogger("Slither")
logging.basicConfig()

class Slither(Context):
    """
    Slither static analyzer
    """

    def __init__(self):
        super(Slither, self).__init__()
        self._contracts = {}
        self._filename = None
        self._source_units = {}
        self._solc_version = None  # '0.3' or '0.4':!
        self._pragma_directives = []
        self._import_directives = []
        self._raw_source_code = {}
        self._all_functions = set()
        self._all_modifiers = set()
        self._all_state_variables = None

        self._previous_results_filename = 'slither.db.json'
        self._results_to_hide = []
        self._previous_results = []
        self._previous_results_ids = set()
        self._paths_to_filter = set()

        self._crytic_compile = None

        self._generate_patches = False
        self._exclude_dependencies = False

        self._markdown_root = ""

        self._contract_name_collisions = defaultdict(list)
        self._contract_with_missing_inheritance = set()

    ###################################################################################
    ###################################################################################
    # region Source code
    ###################################################################################
    ###################################################################################

    @property
    def source_code(self):
        """ {filename: source_code (str)}: source code """
        return self._raw_source_code

    @property
    def source_units(self):
        return self._source_units

    @property
    def filename(self):
        """str: Filename."""
        return self._filename

    def _add_source_code(self, path):
        """
        :param path:
        :return:
        """
        if self.crytic_compile and path in self.crytic_compile.src_content:
            self.source_code[path] = self.crytic_compile.src_content[path]
        else:
            with open(path, encoding='utf8', newline='') as f:
                self.source_code[path] = f.read()

    @property
    def markdown_root(self):
        return self._markdown_root

    # endregion
    ###################################################################################
    ###################################################################################
    # region Pragma attributes
    ###################################################################################
    ###################################################################################

    @property
    def solc_version(self):
        """str: Solidity version."""
        if self.crytic_compile:
            return self.crytic_compile.compiler_version.version
        return self._solc_version

    @property
    def pragma_directives(self):
        """ list(core.declarations.Pragma): Pragma directives."""
        return self._pragma_directives

    @property
    def import_directives(self):
        """ list(core.declarations.Import): Import directives"""
        return self._import_directives

    # endregion
    ###################################################################################
    ###################################################################################
    # region Contracts
    ###################################################################################
    ###################################################################################

    @property
    def contracts(self):
        """list(Contract): List of contracts."""
        return list(self._contracts.values())

    @property
    def contracts_derived(self):
        """list(Contract): List of contracts that are derived and not inherited."""
        inheritance = (x.inheritance for x in self.contracts)
        inheritance = [item for sublist in inheritance for item in sublist]
        return [c for c in self._contracts.values() if c not in inheritance]

    def contracts_as_dict(self):
        """list(dict(str: Contract): List of contracts as dict: name -> Contract."""
        return self._contracts

    def get_contract_from_name(self, contract_name):
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
    def functions(self):
        return list(self._all_functions)

    def add_function(self, func):
        self._all_functions.add(func)

    @property
    def modifiers(self):
        return list(self._all_modifiers)

    def add_modifier(self, modif):
        self._all_modifiers.add(modif)

    @property
    def functions_and_modifiers(self):
        return self.functions + self.modifiers

    def _propagate_function_calls(self):
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
    def state_variables(self):
        if self._all_state_variables is None:
            state_variables = [c.state_variables for c in self.contracts]
            state_variables = [item for sublist in state_variables for item in sublist]
            self._all_state_variables = set(state_variables)
        return list(self._all_state_variables)

    # endregion
    ###################################################################################
    ###################################################################################
    # region Export
    ###################################################################################
    ###################################################################################

    def print_functions(self, d):
        """
            Export all the functions to dot files
        """
        for c in self.contracts:
            for f in c.functions:
                f.cfg_to_dot(os.path.join(d, '{}.{}.dot'.format(c.name, f.name)))

    # endregion
    ###################################################################################
    ###################################################################################
    # region Filtering results
    ###################################################################################
    ###################################################################################

    def relative_path_format(self, path):
        """
           Strip relative paths of "." and ".."
        """
        return path.split('..')[-1].strip('.').strip('/')

    def valid_result(self, r):
        '''
            Check if the result is valid
            A result is invalid if:
                - All its source paths belong to the source path filtered
                - Or a similar result was reported and saved during a previous run
                - The --exclude-dependencies flag is set and results are only related to dependencies
        '''
        source_mapping_elements = [elem['source_mapping']['filename_absolute']
                                   for elem in r['elements'] if 'source_mapping' in elem]
        source_mapping_elements = map(lambda x: os.path.normpath(x) if x else x, source_mapping_elements)
        matching = False

        for path in self._paths_to_filter:
            try:
                if any(bool(re.search(self.relative_path_format(path), src_mapping))
                       for src_mapping in source_mapping_elements):
                    matching = True
                    break
            except re.error:
                logger.error(f'Incorrect regular expression for --filter-paths {path}.'
                             '\nSlither supports the Python re format'
                             ': https://docs.python.org/3/library/re.html')

        if r['elements'] and matching:
            return False
        if r['elements'] and self._exclude_dependencies:
            return not all(element['source_mapping']['is_dependency'] for element in r['elements'])
        if r['id'] in self._previous_results_ids:
            return False
        # Conserve previous result filtering. This is conserved for compatibility, but is meant to be removed
        return not r['description'] in [pr['description'] for pr in self._previous_results]

    def load_previous_results(self):
        filename = self._previous_results_filename
        try:
            if os.path.isfile(filename):
                with open(filename) as f:
                    self._previous_results = json.load(f)
                    if self._previous_results:
                        for r in self._previous_results:
                            if 'id' in r:
                                self._previous_results_ids.add(r['id'])
        except json.decoder.JSONDecodeError:
            logger.error(red('Impossible to decode {}. Consider removing the file'.format(filename)))

    def write_results_to_hide(self):
        if not self._results_to_hide:
            return
        filename = self._previous_results_filename
        with open(filename, 'w', encoding='utf8') as f:
            results = self._results_to_hide + self._previous_results
            json.dump(results, f)

    def save_results_to_hide(self, results):
        self._results_to_hide += results

    def add_path_to_filter(self, path):
        '''
            Add path to filter
            Path are used through direct comparison (no regex)
        '''
        self._paths_to_filter.add(path)

    # endregion
    ###################################################################################
    ###################################################################################
    # region Crytic compile
    ###################################################################################
    ###################################################################################

    @property
    def crytic_compile(self):
        return self._crytic_compile

    # endregion
    ###################################################################################
    ###################################################################################
    # region Format
    ###################################################################################
    ###################################################################################

    @property
    def generate_patches(self):
        return self._generate_patches

    @generate_patches.setter
    def generate_patches(self, p):
        self._generate_patches = p


    # endregion
    ###################################################################################
    ###################################################################################
    # region Internals
    ###################################################################################
    ###################################################################################

    @property
    def contract_name_collisions(self):
        return self._contract_name_collisions

    @property
    def contracts_with_missing_inheritance(self):
        return self._contract_with_missing_inheritance
    # endregion
