from slither.printers.abstract_printer import AbstractPrinter


class CFG(AbstractPrinter):

    ARGUMENT = "cfg"
    HELP = "Export the CFG of each functions"

    WIKI = "https://github.com/trailofbits/slither/wiki/Printer-documentation#cfg"

    def output(self, filename):
        """
        _filename is not used
        Args:
            _filename(string)
        """

        info = ""
        all_files = []
        for contract in self.contracts:
            if contract.is_top_level:
                continue
            for function in contract.functions + contract.modifiers:
                if filename:
                    new_filename = "{}-{}-{}.dot".format(
                        filename, contract.name, function.full_name
                    )
                else:
                    new_filename = "{}-{}.dot".format(contract.name, function.full_name)
                info += "Export {}\n".format(new_filename)
                content = function.slithir_cfg_to_dot_str()
                with open(new_filename, "w", encoding="utf8") as f:
                    f.write(content)
                all_files.append((new_filename, content))

        self.info(info)

        res = self.generate_output(info)
        for filename_result, content in all_files:
            res.add_file(filename_result, content)
        return res
