"""
    Module printing the high level calls
"""
from slither.printers.abstract_printer import AbstractPrinter
from slither.utils.myprettytable import MyPrettyTable


class ExternalCallPrinter(AbstractPrinter):

    ARGUMENT = "external-calls"
    HELP = "Print the external calls performed by each function"

    WIKI = "https://github.com/trailofbits/slither/wiki/Printer-documentation#external-calls"

    def output(self, _):
        """Computes and returns the list of external calls performed."""

        all_txt = "External calls"

        table = MyPrettyTable(["Source (Line)", "Destination", "Chain"])

        # pylint: disable=too-many-nested-blocks
        for contract in self.slither.contracts:
            if contract.is_interface or contract.is_abstract:
                continue

            for function in contract.functions:
                # Bail out early if this function does not perform high level calls
                if not function.all_high_level_calls():
                    continue

                for node in function.nodes:
                    for target_contract, target_function in node.high_level_calls:

                        row = [
                            f"{function.canonical_name} {node.source_mapping.to_detailed_str()}",
                            f"{target_contract.name}.{target_function}",
                        ]

                        if function.all_reachable_from_functions:

                            for source in function.all_reachable_from_functions:
                                chain = f"{source.canonical_name} -> {function.canonical_name}"
                                table.add_row(
                                    [
                                        *row,
                                        chain,
                                    ]
                                )
                        else:
                            table.add_row([*row, ""])

        all_txt += "\n" + str(table)
        self.info(all_txt)

        res = self.generate_output(all_txt)
        res.add_pretty_table(table, "External Calls")

        return res
