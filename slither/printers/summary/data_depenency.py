"""
    Module printing summary of the contract
"""

from slither.printers.abstract_printer import AbstractPrinter
from slither.analyses.data_dependency.data_dependency import get_dependencies
from slither.slithir.variables import TemporaryVariable, ReferenceVariable
from slither.utils.myprettytable import MyPrettyTable


def _get(v, c):
    return list(
        {
            d.name
            for d in get_dependencies(v, c)
            if not isinstance(d, (TemporaryVariable, ReferenceVariable))
        }
    )


class DataDependency(AbstractPrinter):

    ARGUMENT = "data-dependency"
    HELP = "Print the data dependencies of the variables"

    WIKI = "https://github.com/trailofbits/slither/wiki/Printer-documentation#data-dependencies"

    def output(self, _filename):
        """
            _filename is not used
            Args:
                _filename(string)
        """

        all_tables = []
        all_txt = ""

        txt = ""
        for c in self.contracts:
            if c.is_top_level:
                continue
            txt += "\nContract %s\n" % c.name
            table = MyPrettyTable(["Variable", "Dependencies"])
            for v in c.state_variables:
                table.add_row([v.name, _get(v, c)])

            txt += str(table)

            txt += "\n"
            for f in c.functions_and_modifiers_declared:
                txt += "\nFunction %s\n" % f.full_name
                table = MyPrettyTable(["Variable", "Dependencies"])
                for v in f.variables:
                    table.add_row([v.name, _get(v, f)])
                for v in c.state_variables:
                    table.add_row([v.canonical_name, _get(v, f)])
                txt += str(table)
            self.info(txt)

            all_txt += txt
            all_tables.append((c.name, table))

        res = self.generate_output(all_txt)
        for name, table in all_tables:
            res.add_pretty_table(table, name)

        return res
