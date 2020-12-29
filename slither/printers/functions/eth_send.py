from slither.printers.abstract_printer import AbstractPrinter
from slither.utils.myprettytable import MyPrettyTable
from slither.utils.output import Output


class EthSendPrinter(AbstractPrinter):

    ARGUMENT = "eth-send"
    HELP = "Print all functions that can send ETH"

    WIKI = "https://github.com/trailofbits/slither/wiki/Printer-documentation#eth-send"

    def output(self, _filename: str) -> Output:
        txt = ""
        all_tables = []
        for contract in self.slither.contracts:
            if contract.is_top_level:
                continue
            functions = [f for f in contract.functions if f.can_send_eth()]
            if functions:
                txt += f"\n{contract.name}:\n"
                table = MyPrettyTable(["Name"])
                for function in functions:
                    table.add_row([f"{function.solidity_signature} {function.visibility}"])
                txt += str(table) + "\n"
                all_tables.append((contract.name, table))

        self.info(txt)

        res = self.generate_output(txt)
        for name, table in all_tables:
            res.add_pretty_table(table, name)

        return res
