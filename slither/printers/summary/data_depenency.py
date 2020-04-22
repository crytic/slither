"""
    Module printing summary of the contract
"""

from slither.printers.abstract_printer import AbstractPrinter
from slither.analyses.data_dependency.data_dependency import pprint_dependency_table



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
            #print(pprint_dependency(c))
            txt += "\nContract %s\n"%c.name
            table = pprint_dependency_table(c)

            txt += str(table)

            txt += "\n"
            for f in c.functions_and_modifiers_declared:
                txt += "\nFunction %s\n"%f.full_name
                table = pprint_dependency_table(f)
                txt += str(table)
            self.info(txt)

            all_txt += txt
            all_tables.append((c.name, table))

        res = self.generate_output(all_txt)
        for name, table in all_tables:
            res.add_pretty_table(table, name)

        return res
