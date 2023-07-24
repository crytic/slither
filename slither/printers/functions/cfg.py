from slither.printers.abstract_printer import AbstractPrinter
from slither.utils.output import Output


class CFG(AbstractPrinter):

    ARGUMENT = "cfg"
    HELP = "Export the CFG of each functions"

    WIKI = "https://github.com/trailofbits/slither/wiki/Printer-documentation#cfg"

    def output(self, filename: str) -> Output:
        """
        _filename is not used
        Args:
            _filename(string)
        """

        info = ""
        all_files = []
        for contract in self.contracts:  # type: ignore
            for function in contract.functions + list(contract.modifiers):
                if filename:
                    new_filename = f"{filename}-{contract.name}-{function.full_name}.dot"
                else:
                    new_filename = f"{contract.name}-{function.full_name}.dot"
                info += f"Export {new_filename}\n"
                content = function.slithir_cfg_to_dot_str()
                with open(new_filename, "w", encoding="utf8") as f:
                    f.write(content)
                all_files.append((new_filename, content))

        self.info(info)

        res = self.generate_output(info)
        for filename_result, content in all_files:
            res.add_file(filename_result, content)
        return res
