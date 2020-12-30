from typing import Iterator

from slither.printers.abstract_printer import AbstractPrinter
from slither.utils.myprettytable import MyPrettyTable
from slither.utils.output import Output
from slither.slithir.operations import Operation, Call
from slither.core.declarations import Function, Contract


def operations_that_send_ether(function: Function) -> Iterator[Operation]:
    for ir in function.all_slithir_operations():
        if isinstance(ir, Call) and ir.can_send_eth():
            yield ir


class EthSendPrinter(AbstractPrinter):

    ARGUMENT = "eth-send"
    HELP = "Print all functions that can send ETH and the statements that can send ether"

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
                table = MyPrettyTable(["Name", "Statement"])
                for function in functions:
                    table.add_row(
                        [
                            f"{function.solidity_signature} {function.visibility}",
                            "\n".join(
                                str(ir.expression) for ir in operations_that_send_ether(function)
                            ),
                        ]
                    )
                txt += str(table) + "\n"
                all_tables.append((contract.name, table))

        self.info(txt)

        res = self.generate_output(txt)
        for name, table in all_tables:
            res.add_pretty_table(table, name)

        return res
