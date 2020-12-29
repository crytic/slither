from slither.printers.abstract_printer import AbstractPrinter
from slither.utils.myprettytable import MyPrettyTable


class EthReceivePrinter(AbstractPrinter):

    ARGUMENT = "eth-receive"
    HELP = "Print all functions that can receive ether"

    WIKI = "https://github.com/trailofbits/slither/wiki/Printer-documentation#eth-receive"

    def output(self, _filename: str):
        txt = ""
        all_tables = []
        for contract in self.slither.contracts:
            if contract.is_top_level:
                continue
            payable_functions = [f for f in contract.functions if f.payable]
            if payable_functions:
                txt += f"\n{contract.name}:\n"
                table = MyPrettyTable(["Name"])
                for function in payable_functions:
                    table.add_row([function.solidity_signature])
                txt += str(table) + "\n"
                all_tables.append((contract.name, table))

        self.info(txt)

        res = self.generate_output(txt)
        for name, table in all_tables:
            res.add_pretty_table(table, name)

        return res
