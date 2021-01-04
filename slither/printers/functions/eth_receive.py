from slither.printers.abstract_printer import AbstractPrinter
from slither.utils.myprettytable import MyPrettyTable
from slither.utils.output import Output
from slither.slithir.operations import Operation
from slither.core.cfg.node import Node


# TODO requirements

MSG_VALUE_OR_SENDER = set(["msg.value", "msg.sender"])

def is_reading_msg_value_or_sender(node: Node) -> bool:
    return any(v.name in MSG_VALUE_OR_SENDER for v in node.solidity_variables_read)


def is_dominated_by_msg_value_or_sender(node: Node) -> bool:
    return any(is_reading_msg_value_or_sender(n) for n in node.dominators)



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
                table = MyPrettyTable(["Name", "Side effects dependent on msg.value or msg.sender", "Requirements"])
                for function in payable_functions:
                    dominated_by_msg_value_or_sender = [
                        n for n in function.nodes if is_dominated_by_msg_value_or_sender(n) if n.expression and not n.contains_require_or_assert()
                    ]
                    requirements = [
                        n for n in function.nodes if n.contains_require_or_assert() and is_dominated_by_msg_value_or_sender(n)
                    ]

                    table.add_row(
                        [
                            function.solidity_signature,
                            "\n".join(str(n.expression) for n in dominated_by_msg_value_or_sender),
                            "\n".join(str(n.expression) for n in requirements),
                        ]
                    )
                txt += str(table) + "\n"
                all_tables.append((contract.name, table))

        self.info(txt)

        res = self.generate_output(txt)
        for name, table in all_tables:
            res.add_pretty_table(table, name)

        return res
