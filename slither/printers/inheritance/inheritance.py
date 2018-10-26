"""
    Module printing the inheritance relation

    The inheritance shows the relation between the contracts
"""

from slither.printers.abstract_printer import AbstractPrinter
from slither.utils.colors import blue, green


class PrinterInheritance(AbstractPrinter):
    ARGUMENT = 'inheritance'
    HELP = 'Print the inheritance relations between contracts'

    def _get_child_contracts(self, base):
        # Generate function to get all child contracts of a base contract
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

        if not self.contracts:
            return

        info += blue('Child_Contract -> ') + green('Base_Contracts')
        for child in self.contracts:
            info += blue(f'\n+ {child.name}')
            if child.inheritance:
                info += ' -> ' + green(", ".join(map(str, child.inheritance)))

        info += green('\n\nBase_Contract -> ') + blue('Child_Contracts')
        for base in self.contracts:
            info += green(f'\n+ {base.name}')
            children = list(self._get_child_contracts(base))
            if children:
                info += ' -> ' + blue(", ".join(map(str, children)))
        self.info(info)
