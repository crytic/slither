"""
    Module printing summary of the contract
"""

from prettytable import PrettyTable
from slither.printers.abstract_printer import AbstractPrinter
from slither.analyses.data_dependency.data_dependency import get_dependencies
from slither.slithir.variables import TemporaryVariable, ReferenceVariable

def _get(v, c):
    return list(set([d.name for d in get_dependencies(v, c) if not isinstance(d, (TemporaryVariable,
                                                                               ReferenceVariable))]))

class DataDependency(AbstractPrinter):

    ARGUMENT = 'data-dependency'
    HELP = 'Print the data dependencies of the variables'

    WIKI = 'https://github.com/trailofbits/slither/wiki/Printer-documentation#data-dependencies'

    def output(self, _filename):
        """
            _filename is not used
            Args:
                _filename(string)
        """

        txt = ''
        for c in self.contracts:
            txt += "\nContract %s\n"%c.name
            table = PrettyTable(['Variable', 'Dependencies'])
            for v in c.state_variables:
                table.add_row([v.name, _get(v, c)])

            txt += str(table)

            txt += "\n"
            for f in c.functions_and_modifiers_declared:
                txt += "\nFunction %s\n"%f.full_name
                table = PrettyTable(['Variable', 'Dependencies'])
                for v in f.variables:
                    table.add_row([v.name, _get(v, f)])
                for v in c.state_variables:
                    table.add_row([v.canonical_name, _get(v, f)])
                txt += str(table)
            self.info(txt)
