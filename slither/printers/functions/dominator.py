from typing import List

from slither.core.declarations import Function
from slither.printers.abstract_printer import AbstractPrinter


class Dominator(AbstractPrinter):

    ARGUMENT = "dominator"
    HELP = "Export the dominator tree of each functions"

    WIKI = "https://github.com/trailofbits/slither/wiki/Printer-documentation#dominator"

    def output(self, filename):
        """
        _filename is not used
        Args:
            _filename(string)
        """

        info = ""
        all_files = []
        for contract in self.contracts:
            for function in contract.functions + contract.modifiers:
                if filename:
                    new_filename = f"{filename}-{contract.name}-{function.full_name}.dot"
                else:
                    new_filename = f"dominator-{contract.name}-{function.full_name}.dot"
                info += f"Export {new_filename}\n"
                content = function.dominator_tree_to_dot(new_filename)
                all_files.append((new_filename, content))

        self.info(info)

        res = self.generate_output(info)
        for filename_result, content in all_files:
            res.add_file(filename_result, content)
        return res
