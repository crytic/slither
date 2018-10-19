"""
    Module printing the inheritance relation

    The inheritance shows the relation between the contracts
"""

from slither.printers.abstract_printer import AbstractPrinter
from slither.utils.colors import blue, green, magenta


class PrinterInheritance(AbstractPrinter):
    ARGUMENT = 'inheritance'
    HELP = 'the inheritance relation between contracts'

    def _get_child_contracts(self, base):
        for child in self.contracts:
            if base in child.inheritance:
                yield child

    def output(self, filename):
        """
            Output the inheritance relation

            _filename is not used
            Args:
                _filename(string)
        """
        info = 'Inheritance\n'
        info += blue('Child_Contract -> ') + green('Base_Contracts')
        for contract in self.contracts:
            info += blue(f'\n+ {contract.name} -> ')
            if contract.inheritance:
                info += green(", ".join(map(str, contract.inheritance)))
            else:
                info += magenta("Root_Contract")

        info += green('\n\nBase_Contract -> ') + blue('Child_Contracts')
        for contract in self.contracts:
            info += green(f'\n+ {contract.name} -> ')
            children = list(self._get_child_contracts(contract))
            if children:
                info += blue(", ".join(map(str, children)))
            else:
                info += magenta("Leaf_Contract")
        self.info(info)
