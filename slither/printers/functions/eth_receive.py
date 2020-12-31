from slither.printers.abstract_printer import AbstractPrinter
from slither.utils.myprettytable import MyPrettyTable
from slither.utils.output import Output
from slither.slithir.operations import Operation

MSG_SENDER_AND_VALUE = set(["msg.sender", "msg.value"])


def reads_msg_sender_or_value(ir: Operation) -> bool:
    return any(str(var) in MSG_SENDER_AND_VALUE for var in ir.read)


class EthReceivePrinter(AbstractPrinter):

    ARGUMENT = "eth-receive"
    HELP = "Print all functions that can receive ETH"

    WIKI = "https://github.com/trailofbits/slither/wiki/Printer-documentation#eth-receive"

    def output(self, _filename: str) -> Output:
        txt = ""
        all_tables = []
        for contract in self.slither.contracts:
            if contract.is_top_level or contract.is_interface:
                continue
            payable_functions = [f for f in contract.functions if f.payable]
            if payable_functions:
                txt += f"\n{contract.name}:\n"
                table = MyPrettyTable(["Name", "Relevant Expressions"])
                for function in payable_functions:
                    relevant_expressions = [
                        ir
                        for ir in function.all_slithir_operations()
                        if reads_msg_sender_or_value(ir)
                    ]
                    table.add_row(
                        [
                            function.solidity_signature,
                            "\n".join(str(ir.expression) for ir in relevant_expressions),
                        ]
                    )
                txt += str(table) + "\n"
                all_tables.append((contract.name, table))

        self.info(txt)

        res = self.generate_output(txt)
        for name, table in all_tables:
            res.add_pretty_table(table, name)

        return res
