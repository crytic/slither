"""
    Main module
"""
import os
from slither.core.context.context import Context
from slither.slithir.operations import InternalCall
import json

class Slither(Context):
    """
    Slither static analyzer
    """

    def __init__(self):
        super(Slither, self).__init__()
        self._contracts = {}
        self._filename = None
        self._source_units = {}
        self._solc_version = None # '0.3' or '0.4':!
        self._pragma_directives = []
        self._import_directives = []
        self._raw_source_code = {}
        self._all_functions = set()
        self._all_modifiers = set()

        self._previous_descriptions = set()
        self._paths_to_filter = set()


    ###################################################################################
    ###################################################################################
    # region Source code
    ###################################################################################
    ###################################################################################

    @property
    def source_code(self):
        """ {filename: source_code}: source code """
        return self._raw_source_code

    @property
    def source_units(self):
        return self._source_units

    @property
    def filename(self):
        """str: Filename."""
        return self._filename

    # endregion
    ###################################################################################
    ###################################################################################
    # region Pragma attributes
    ###################################################################################
    ###################################################################################

    @property
    def solc_version(self):
        """str: Solidity version."""
        return self._solc_version

    @property
    def pragma_directives(self):
        """ list(list(str)): Pragma directives. Example [['solidity', '^', '0.4', '.24']]"""
        return self._pragma_directives

    @property
    def import_directives(self):
        """ list(str): Import directives"""
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

    def valid_result(self, r):
        '''
            Check if the result is valid
            A result is invalid if:
                - All its source paths belong to the source path filtered
                - Or a similar result was reported and saved during a previous run
        '''
        if r['elements'] and all((any(path in elem['source_mapping']['filename'] for path in self._paths_to_filter) for elem in r['elements'])):
            return False
        return not r['description'] in self._previous_descriptions

    def load_previous_results(self, filename='slither.db.json'):
        if os.path.isfile(filename):
            with open(filename) as f:
                data = json.load(f)
                self._previous_descriptions = set(r['description'] for r in data)

    def add_path_to_filter(self, path):
        '''
            Add path to filter
            Path are used through direct comparison (no regex)
        '''
        self._paths_to_filter.add(path)

    # endregion
