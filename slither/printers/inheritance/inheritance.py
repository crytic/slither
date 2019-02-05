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

        info += blue('Child_Contract -> ') + green('Immediate_Base_Contracts')
        info += green(' [Not_Immediate_Base_Contracts]')
        for child in self.contracts:
            info += blue(f'\n+ {child.name}')
            if child.inheritance:
                immediate = child.immediate_inheritance
                not_immediate = [i for i in child.inheritance if i not in immediate]
                info += ' -> ' + green(", ".join(map(str, immediate)))
                if not_immediate:
                    info += ", ["+ green(", ".join(map(str, not_immediate))) + "]"

        info += green('\n\nBase_Contract -> ') + blue('Immediate_Child_Contracts')
        info += blue(' [Not_Immediate_Child_Contracts]')
        for base in self.contracts:
            info += green(f'\n+ {base.name}')
            children = list(self._get_child_contracts(base))
            if children:
                immediate = [child for child in children if base in child.immediate_inheritance]
                not_immediate = [child for child in children if not child in immediate]
                info += ' -> ' + blue(", ".join(map(str, immediate)))
                if not_immediate:
                    info += ', [' + blue(", ".join(map(str, not_immediate))) + ']'
        self.info(info)
