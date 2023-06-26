"""
    Module printing summary of the contract
"""
from typing import List

from slither.core.declarations import Contract
from slither.printers.abstract_printer import AbstractPrinter
from slither.analyses.data_dependency.data_dependency import get_dependencies, SUPPORTED_TYPES
from slither.slithir.variables import TemporaryVariable, ReferenceVariable
from slither.utils.myprettytable import MyPrettyTable
from slither.utils.output import Output


def _get(v: SUPPORTED_TYPES, c: Contract) -> List[str]:
    return list(
        {
            d.name
            for d in get_dependencies(v, c)
            if not isinstance(d, (TemporaryVariable, ReferenceVariable)) and d.name
        }
    )


class DataDependency(AbstractPrinter):

    ARGUMENT = "data-dependency"
    HELP = "Print the data dependencies of the variables"

    WIKI = "https://github.com/trailofbits/slither/wiki/Printer-documentation#data-dependencies"

    def output(self, _filename: str) -> Output:
        """
        _filename is not used
        Args:
            _filename(string)
        """

        all_tables = []
        all_txt = ""

        txt = ""
        for c in self.contracts:
            txt += f"\nContract {c.name}\n"
            table = MyPrettyTable(["Variable", "Dependencies"])
            for v in c.state_variables:
                assert v.name
                table.add_row([v.name, sorted(_get(v, c))])

            txt += str(table)

            txt += "\n"
            for f in c.functions_and_modifiers_declared:
                txt += f"\nFunction {f.full_name}\n"
                table = MyPrettyTable(["Variable", "Dependencies"])
                for v in f.variables:
                    table.add_row([v.name, sorted(_get(v, f))])
                for v in c.state_variables:
                    table.add_row([v.canonical_name, sorted(_get(v, f))])
                txt += str(table)
            self.info(txt)

            all_txt += txt
            all_tables.append((c.name, table))

        res = self.generate_output(all_txt)
        for name, table in all_tables:
            res.add_pretty_table(table, name)

        return res
