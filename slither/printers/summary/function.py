"""
    Module printing summary of the contract
"""

from slither.printers.abstract_printer import AbstractPrinter
from slither.utils.myprettytable import MyPrettyTable


class FunctionSummary(AbstractPrinter):

    ARGUMENT = "function-summary"
    HELP = "Print a summary of the functions"

    WIKI = "https://github.com/trailofbits/slither/wiki/Printer-documentation#function-summary"

    @staticmethod
    def _convert(l):
        if l:
            n = 2
            l = [l[i : i + n] for i in range(0, len(l), n)]
            l = [str(x) for x in l]
            return "\n".join(l)
        return str(l)

    def output(self, _filename):  # pylint: disable=too-many-locals
        """
        _filename is not used
        Args:
            _filename(string)
        """

        all_tables = []
        all_txt = ""

        for c in self.contracts:
            if c.is_top_level:
                continue
            (name, inheritance, var, func_summaries, modif_summaries) = c.get_summary()
            txt = f"\nContract {name}"
            txt += "\nContract vars: " + str(var)
            txt += "\nInheritance:: " + str(inheritance)
            table = MyPrettyTable(
                [
                    "Function",
                    "Visibility",
                    "Modifiers",
                    "Read",
                    "Write",
                    "Internal Calls",
                    "External Calls",
                ]
            )
            for (
                _c_name,
                f_name,
                visi,
                modifiers,
                read,
                write,
                internal_calls,
                external_calls,
            ) in func_summaries:
                read = self._convert(read)
                write = self._convert(write)
                internal_calls = self._convert(internal_calls)
                external_calls = self._convert(external_calls)
                table.add_row(
                    [
                        f_name,
                        visi,
                        modifiers,
                        read,
                        write,
                        internal_calls,
                        external_calls,
                    ]
                )
            txt += "\n \n" + str(table)
            table = MyPrettyTable(
                [
                    "Modifiers",
                    "Visibility",
                    "Read",
                    "Write",
                    "Internal Calls",
                    "External Calls",
                ]
            )
            for (
                _c_name,
                f_name,
                visi,
                _,
                read,
                write,
                internal_calls,
                external_calls,
            ) in modif_summaries:
                read = self._convert(read)
                write = self._convert(write)
                internal_calls = self._convert(internal_calls)
                external_calls = self._convert(external_calls)
                table.add_row([f_name, visi, read, write, internal_calls, external_calls])
            txt += "\n\n" + str(table)
            txt += "\n"
            self.info(txt)

            all_tables.append((name, table))
            all_txt += txt

        res = self.generate_output(all_txt)
        for name, table in all_tables:
            res.add_pretty_table(table, name)

        return res
