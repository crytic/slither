"""
    Module printing summary of the contract
"""
from typing import List

from slither.printers.abstract_printer import AbstractPrinter
from slither.core.declarations.function import Function
from slither.utils.myprettytable import MyPrettyTable
from slither.utils.output import Output


class PrinterWrittenVariablesAndAuthorization(AbstractPrinter):

    ARGUMENT = "vars-and-auth"
    HELP = "Print the state variables written and the authorization of the functions"

    WIKI = "https://github.com/trailofbits/slither/wiki/Printer-documentation#variables-written-and-authorization"

    @staticmethod
    def get_msg_sender_checks(function: Function) -> List[str]:
        all_functions = (
            [f for f in function.all_internal_calls() if isinstance(f, Function)]
            + [function]
            + [m for m in function.modifiers if isinstance(m, Function)]
        )

        all_nodes_ = [f.nodes for f in all_functions]
        all_nodes = [item for sublist in all_nodes_ for item in sublist]

        all_conditional_nodes = [
            n for n in all_nodes if n.contains_if() or n.contains_require_or_assert()
        ]
        all_conditional_nodes_on_msg_sender = [
            str(n.expression)
            for n in all_conditional_nodes
            if "msg.sender" in [v.name for v in n.solidity_variables_read]
        ]
        return all_conditional_nodes_on_msg_sender

    def output(self, _filename: str) -> Output:
        """
        _filename is not used
        Args:
            _filename(string)
        """

        txt = ""
        all_tables = []
        for contract in self.contracts:  # type: ignore
            txt += f"\nContract {contract.name}\n"
            table = MyPrettyTable(
                ["Function", "State variables written", "Conditions on msg.sender"]
            )
            for function in contract.functions:

                state_variables_written = [
                    v.name for v in function.all_state_variables_written() if v.name
                ]
                msg_sender_condition = self.get_msg_sender_checks(function)
                table.add_row(
                    [
                        function.name,
                        str(sorted(state_variables_written)),
                        str(sorted(msg_sender_condition)),
                    ]
                )
            all_tables.append((contract.name, table))
            txt += str(table) + "\n"

        self.info(txt)
        res = self.generate_output(txt)
        for name, table in all_tables:
            res.add_pretty_table(table, name)

        return res
