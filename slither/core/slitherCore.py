"""
    Main module
"""
import os

class Slither:
    """
    Slither static analyzer
    """
    name_class = 'Slither'

    def __init__(self):
        self._contracts = {}
        self._filename = None
        self._source_units = {}
        self._solc_version = None # '0.3' or '0.4':!

    @property
    def contracts(self):
        """list(Contract): List of contracts."""
        return list(self._contracts.values())

    @property
    def contracts_derived(self):
        """list(Contract): List of contracts that are derived and not inherited."""
        inheritances = (x.inheritances for x in self.contracts)
        inheritances = (item for sublist in inheritances for item in sublist)
        return [c for c in self._contracts.values() if c not in inheritances]

    def contracts_as_dict(self):
        """list(dict(str: Contract): List of contracts as dict: name -> Contract."""
        return self._contracts

    @property
    def filename(self):
        """str: Filename."""
        return self._filename

    @property
    def solc_version(self):
        """str: Solidity version."""
        return self._solc_version

    def get_contract_from_name(self, contract_name):
        """
            Return a contract from a name
        Args:
            contract_name (str): name of the contract
        Returns:
            Contract
        """
        return next((c for c in self.contracts if c.name == contract_name), None)

    def print_functions(self, d):
        """
            Export all the functions to dot files
        """
        for c in self.contracts:
            for f in c.functions:
                f.cfg_to_dot(os.path.join(d,'{}.{}.dot'.format(c.name, f.name)))
