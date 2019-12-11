"""
    Module printing summary of the contract
"""

from prettytable import PrettyTable

from slither.core.declarations import Structure
from slither.core.solidity_types import UserDefinedType
from slither.printers.abstract_printer import AbstractPrinter
from slither.analyses.data_dependency.data_dependency import get_dependencies, pprint_dependency
from slither.slithir.variables import TemporaryVariable, IndexVariable, Constant, MemberVariable


def _convert(d):
    if isinstance(d, tuple):
        return '.'.join([x.name for x in d])
    return d.name

def _get(v, c):
    return list(set([_convert(d) for d in get_dependencies(v, c) if not isinstance(d, (TemporaryVariable,
                                                                              IndexVariable, MemberVariable, tuple))]))

def add_row(v, c, table):
    if isinstance(v.type, UserDefinedType) and isinstance(v.type.type, Structure):
        for elem in v.type.type.elems.values():
            if isinstance(elem.type, UserDefinedType) and isinstance(elem.type.type, Structure):
                for elem_nested in elem.type.type.elems.values():
                    table.add_row([f'{v.name}.{elem}.{elem_nested.name}', _get([v, Constant(elem.name), Constant(elem_nested.name)], c)])
            else:
                table.add_row([f'{v.name}.{elem}', _get((v, Constant(elem.name)), c)])
    else:
        table.add_row([v.name, _get(v, c)])

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

        all_tables = []
        all_txt = ''

        txt = ''
        #print(pprint_dependency(c))
        for c in self.contracts:
            print(pprint_dependency(c))
            txt += "\nContract %s\n"%c.name
            table = PrettyTable(['Variable', 'Dependencies'])
            for v in c.state_variables:
                add_row(v, c, table)

            txt += str(table)

            txt += "\n"
            for f in c.functions_and_modifiers_declared:
                txt += "\nFunction %s\n"%f.full_name
                table = PrettyTable(['Variable', 'Dependencies'])
                for v in f.variables:
                    add_row(v, f, table)
                for v in c.state_variables:
                    add_row(v, f, table)
                txt += str(table)
            self.info(txt)

            all_txt += txt
            all_tables.append((c.name, table))

        res = self.generate_output(all_txt)
        for name, table in all_tables:
            res.add_pretty_table(table, name)

        return res
